# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

import sqlite3

from hompi import db


def _table_names(path):
    return {
        row[0]
        for row in sqlite3.connect(path).execute(
            "select name from sqlite_master where type='table'"
        )
    }


def _configure_tmpfs(home, tmpfs, monkeypatch):
    monkeypatch.setattr(db.paths, 'data_dir', lambda: home)
    monkeypatch.setattr(
        db.paths, 'migrations_dir', lambda: db.paths._packaged_migrations_dir()
    )
    monkeypatch.setattr(db.config, 'TMPFS_ENABLE', True)
    monkeypatch.setattr(db.config, 'TMPFS_PATH', str(tmpfs) + '/')
    db.persistent_db_path = str(home / 'db' / 'hompi.sqlite')
    db.db_path = db.persistent_db_path


def test_connect_uses_wal_and_foreign_keys(tmp_path, monkeypatch):
    monkeypatch.setattr(db.paths, 'data_dir', lambda: tmp_path)
    db_path = tmp_path / 'db' / 'hompi.sqlite'
    db_path.parent.mkdir(parents=True)
    sqlite3.connect(db_path).close()

    conn = db._connect(str(db_path))
    try:
        assert conn.execute('pragma foreign_keys').fetchone()[0] == 1
        assert conn.execute('pragma journal_mode').fetchone()[0] == 'wal'
    finally:
        conn.close()


def test_database_manager_opens_with_wal(tmp_path, monkeypatch):
    monkeypatch.setattr(db.paths, 'data_dir', lambda: tmp_path)
    monkeypatch.setattr(db.config, 'TMPFS_ENABLE', False)
    db_path = tmp_path / 'db' / 'hompi.sqlite'
    db_path.parent.mkdir(parents=True)
    sqlite3.connect(db_path).close()

    mgr = db.DatabaseManager()
    try:
        assert mgr.conn.execute('pragma journal_mode').fetchone()[0] == 'wal'
    finally:
        del mgr


def test_migrate_seeds_tmpfs_when_missing_then_flush(tmp_path, monkeypatch):
    """Missing tmpfs: copy persistent → tmpfs, migrate there; flush writes back."""
    home = tmp_path / 'home'
    tmpfs = tmp_path / 'tmpfs'
    home.mkdir()
    (home / 'db').mkdir()
    tmpfs.mkdir()

    persistent = home / 'db' / 'hompi.sqlite'
    runtime = tmpfs / 'hompi.sqlite'
    sqlite3.connect(persistent).close()

    _configure_tmpfs(home, tmpfs, monkeypatch)

    db.migrate()

    assert db.db_path == str(runtime)
    assert 'migration_version' in _table_names(runtime)
    assert 'migration_version' not in _table_names(persistent)

    db.flush()
    assert 'migration_version' in _table_names(persistent)
    assert not runtime.exists()


def test_migrate_keeps_existing_tmpfs_with_runtime_writes(tmp_path, monkeypatch):
    """Restart must not wipe an existing tmpfs DB with newer API writes."""
    home = tmp_path / 'home'
    tmpfs = tmp_path / 'tmpfs'
    home.mkdir()
    (home / 'db').mkdir()
    tmpfs.mkdir()

    persistent = home / 'db' / 'hompi.sqlite'
    runtime = tmpfs / 'hompi.sqlite'
    sqlite3.connect(persistent).close()

    _configure_tmpfs(home, tmpfs, monkeypatch)

    db.migrate()
    # Simulate an API write on the live tmpfs DB
    conn = sqlite3.connect(runtime)
    conn.execute('create table runtime_marker(x integer)')
    conn.commit()
    conn.close()

    # Stale persistent still has no marker; restart must keep tmpfs
    db.migrate()

    assert 'runtime_marker' in _table_names(runtime)
    assert 'runtime_marker' not in _table_names(persistent)

    db.flush()
    assert 'runtime_marker' in _table_names(persistent)


def test_migrate_without_tmpfs_updates_persistent(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    home.mkdir()
    (home / 'db').mkdir()
    persistent = home / 'db' / 'hompi.sqlite'
    sqlite3.connect(persistent).close()

    monkeypatch.setattr(db.paths, 'data_dir', lambda: home)
    monkeypatch.setattr(
        db.paths, 'migrations_dir', lambda: db.paths._packaged_migrations_dir()
    )
    monkeypatch.setattr(db.config, 'TMPFS_ENABLE', False)
    db.persistent_db_path = str(persistent)
    db.db_path = str(persistent)

    db.migrate()

    assert db.db_path == str(persistent)
    assert 'migration_version' in _table_names(persistent)
