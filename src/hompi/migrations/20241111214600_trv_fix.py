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
