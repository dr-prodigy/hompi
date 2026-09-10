# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

import sqlite3

from hompi import db


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
