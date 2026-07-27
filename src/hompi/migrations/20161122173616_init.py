# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

import os
"""
This module contains a Caribou migration.

Migration Name: init 
Migration Version: 20161122173616
"""


# connection is a plain old sqlite3 database connection
def upgrade(connection):

    cursor = connection.cursor()

    scriptFile = open(os.path.dirname(os.path.realpath(__file__)) + "/20161122173616_init.sql", 'r')
    script = scriptFile.read()
    scriptFile.close()
    connection.executescript(script)

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    pass
