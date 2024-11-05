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
