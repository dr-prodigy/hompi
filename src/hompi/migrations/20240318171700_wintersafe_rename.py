# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""
a caribou migration

name: wintersafe_rename
version: 20240318171700
"""


def upgrade(connection):
    sql = "UPDATE `gm_temp` SET description = 'Winter_safe' WHERE description = 'Winter-safe';"
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    sql = "UPDATE `gm_temp` SET description = 'Winter-safe' WHERE description = 'Winter_safe';"
    connection.execute(sql)
    connection.commit()
