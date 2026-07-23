#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C)2018-24 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>.
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

import config

db_name = 'hompi.sqlite'
db_path = persistent_db_path = f'./db/{db_name}'
migrations_path = './migrations'

def __init__():
    global db_path
    if config.TMPFS_ENABLE:
        # move db to temporary filesystem
        tmp_db_path = f'{config.TMPFS_PATH}{db_name}'
        if not os.path.exists(tmp_db_path):
            print(f'Copying {db_path} to {tmp_db_path}')
            shutil.copy2(db_path, tmp_db_path)
        db_path = tmp_db_path

def migrate():
    print(f'Applying migrations to {db_path}')
    # upgrade to most recent version
    caribou.upgrade(db_path, migrations_path)

def flush():
    global db_path, persistent_db_path
    if config.TMPFS_ENABLE:
        # move db back to persistent filesystem
        print(f'Restoring {db_path} to {persistent_db_path}')
        if os.path.exists(persistent_db_path):
            os.remove(persistent_db_path)
        shutil.copy2(db_path, persistent_db_path)
        os.remove(db_path)


class DatabaseManager(object):
    def __init__(self):
        global db_path
        if config.TMPFS_ENABLE:
            # move db to temporary filesystem
            tmp_db_path = f'{config.TMPFS_PATH}{db_name}'
            if not os.path.exists(tmp_db_path):
                shutil.copy2(db_path, tmp_db_path)
            db_path = tmp_db_path

        self.conn = sqlite3.connect(db_path)
        self.conn.execute('pragma foreign_keys = on')
        self.conn.commit()
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
