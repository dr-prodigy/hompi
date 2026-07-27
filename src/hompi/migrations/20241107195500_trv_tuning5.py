# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

import os
"""
a caribou migration

name: trv_tuning5
version: 20241107195500
"""


def upgrade(connection):
    scriptFile = open(os.path.dirname(os.path.realpath(__file__)) + "/20241107195500_trv_tuning5.sql", 'r')
    script = scriptFile.read()
    scriptFile.close()
    connection.executescript(script)

    connection.commit()

def downgrade(connection):
    pass
