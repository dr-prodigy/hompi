#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>
#
# hompi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# hompi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with hompi.  If not, see <http://www.gnu.org/licenses/>.

import caribou
import sqlite3
import shutil
import os

from .config import config
from . import paths

db_name = 'hompi.sqlite'
db_path = persistent_db_path = str(paths.db_file(db_name))
migrations_path = str(paths.migrations_dir())

# Daemon and uWSGI open the same file concurrently; wait instead of failing fast.
SQLITE_TIMEOUT_SEC = 5.0


def _connect(path):
    """Open SQLite with shared-access settings (timeout + WAL)."""
    conn = sqlite3.connect(path, timeout=SQLITE_TIMEOUT_SEC)
    conn.execute('pragma foreign_keys = on')
    conn.execute('pragma journal_mode = wal')
    conn.commit()
    return conn


def _tmpfs_db_path():
    return f'{config.TMPFS_PATH}{db_name}'


def _sqlite_paths(path):
    """Main DB path plus WAL/SHM sidecars."""
    return (path, f'{path}-wal', f'{path}-shm')


def _remove_sqlite_files(path):
    for candidate in _sqlite_paths(path):
        if os.path.exists(candidate):
            os.remove(candidate)


def _checkpoint(path):
    """Flush WAL into the main DB file so a plain copy is consistent."""
    if not os.path.exists(path):
        return
    conn = sqlite3.connect(path, timeout=SQLITE_TIMEOUT_SEC)
    try:
        conn.execute('pragma wal_checkpoint(TRUNCATE)')
        conn.commit()
    finally:
        conn.close()


def _copy_sqlite(src, dst):
    """Copy a SQLite DB safely (checkpoint first; replace dst + sidecars)."""
    _checkpoint(src)
    _remove_sqlite_files(dst)
    shutil.copy2(src, dst)


def _ensure_runtime_db():
    """Point ``db_path`` at the live DB; with TMPFS, seed it from persistent."""
    global db_path, persistent_db_path
    persistent_db_path = str(paths.db_file(db_name))
    os.makedirs(os.path.dirname(persistent_db_path) or '.', exist_ok=True)

    if not config.TMPFS_ENABLE:
        db_path = persistent_db_path
        return db_path

    tmp_db_path = _tmpfs_db_path()
    os.makedirs(os.path.dirname(tmp_db_path) or '.', exist_ok=True)
    if os.path.exists(persistent_db_path):
        print(f'Copying {persistent_db_path} to {tmp_db_path}')
        _copy_sqlite(persistent_db_path, tmp_db_path)
    else:
        # Brand-new install: empty file on tmpfs; migrations create the schema
        _remove_sqlite_files(tmp_db_path)
        sqlite3.connect(tmp_db_path).close()
    db_path = tmp_db_path
    return db_path


def __init__():
    _ensure_runtime_db()


def migrate():
    """Seed TMPFS from persistent (if enabled), then run Caribou on that copy.

    The persistent file is updated later by ``flush()`` when the daemon stops.
    """
    global migrations_path, db_path, persistent_db_path
    migrations_path = str(paths.migrations_dir())
    db_path = _ensure_runtime_db()

    print(f'Applying migrations from {migrations_path} to {db_path}')
    caribou.upgrade(db_path, migrations_path)


def flush():
    """Copy the runtime (tmpfs) DB back to the persistent path on shutdown."""
    global db_path, persistent_db_path
    persistent_db_path = str(paths.db_file(db_name))
    if config.TMPFS_ENABLE and os.path.exists(db_path):
        print(f'Restoring {db_path} to {persistent_db_path}')
        _copy_sqlite(db_path, persistent_db_path)
        _remove_sqlite_files(db_path)


class DatabaseManager(object):
    def __init__(self):
        global db_path, persistent_db_path
        persistent_db_path = str(paths.db_file(db_name))
        if config.TMPFS_ENABLE:
            tmp_db_path = _tmpfs_db_path()
            # After migrate(), tmpfs already holds the live DB. If the API
            # process starts alone, seed from persistent when missing.
            if not os.path.exists(tmp_db_path) and os.path.exists(persistent_db_path):
                _copy_sqlite(persistent_db_path, tmp_db_path)
            db_path = tmp_db_path
        else:
            db_path = persistent_db_path

        self.conn = _connect(db_path)
        self.cur = self.conn.cursor()

    def query(self, command_, args=()):
        try:
            self.cur.execute(command_, args)
        except Exception as e:
            self.conn.rollback()
            raise e
        else:
            self.conn.commit()
        return self.cur

    def insert(self, table, row):
        cols = ', '.join('"{}"'.format(col) for col in row.keys())
        vals = ', '.join(':{}'.format(col) for col in row.keys())
        sql = 'INSERT INTO "{0}" ({1}) VALUES ({2})'.format(table, cols, vals)
        self.cur.execute(sql, row)
        self.conn.commit()

    def __del__(self):
        self.conn.close()
