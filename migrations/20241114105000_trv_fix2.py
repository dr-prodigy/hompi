import os
"""
a caribou migration

name: trv_fix2
version: 20241114105000
"""


def upgrade(connection):
    sql = "UPDATE `gm_timetable_type_data` SET orderby = id - 30 WHERE `id` >= 30"
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    pass
