# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

import os
"""
a caribou migration

name: trv_fix
version: 20241111214600
"""


def upgrade(connection):
    sql = "UPDATE `gm_timetable_type_data` SET orderby = orderby + 1 WHERE `id` in (34, 35)"
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    pass
