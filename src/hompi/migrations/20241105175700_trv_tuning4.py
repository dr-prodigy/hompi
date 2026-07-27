# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

import os
"""
a caribou migration

name: trv_tuning4
version: 20241105175700
"""


def upgrade(connection):
    sql = "UPDATE `gm_timetable_type_data` SET `temp_id` = 2 WHERE `id` = 26"
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    pass
