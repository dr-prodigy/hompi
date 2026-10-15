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


def test_migrate_copies_to_tmpfs_then_migrates_there(tmp_path, monkeypatch):
    """Copy persistent → tmpfs, migrate tmpfs only; persistent waits for flush."""
    home = tmp_path / 'home'
    tmpfs = tmp_path / 'tmpfs'
    home.mkdir()
    (home / 'db').mkdir()
    tmpfs.mkdir()

    persistent = home / 'db' / 'hompi.sqlite'
    runtime = tmpfs / 'hompi.sqlite'

    # Stale leftover on tmpfs must be replaced by the persistent copy first
    conn = sqlite3.connect(runtime)
    conn.execute('create table old_only(x integer)')
    conn.commit()
    conn.close()

    sqlite3.connect(persistent).close()

    monkeypatch.setattr(db.paths, 'data_dir', lambda: home)
    monkeypatch.setattr(
        db.paths, 'migrations_dir', lambda: db.paths._packaged_migrations_dir()
    )
    monkeypatch.setattr(db.config, 'TMPFS_ENABLE', True)
    monkeypatch.setattr(db.config, 'TMPFS_PATH', str(tmpfs) + '/')
    db.persistent_db_path = str(persistent)
    db.db_path = str(persistent)

    db.migrate()

    assert db.db_path == str(runtime)
    runtime_tables = _table_names(runtime)
    assert 'old_only' not in runtime_tables
    assert 'migration_version' in runtime_tables

    # Persistent copy is unchanged until flush()
    assert 'migration_version' not in _table_names(persistent)

    db.flush()
    assert 'migration_version' in _table_names(persistent)
    assert not runtime.exists()


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
