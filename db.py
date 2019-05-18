#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C)2018-19 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
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

db_path = './db/hompi.sqlite'
migrations_path = './migrations'


def migrate():
    # upgrade to most recent version
    caribou.upgrade(db_path, migrations_path)


class DatabaseManager(object):
    def __init__(self):
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
