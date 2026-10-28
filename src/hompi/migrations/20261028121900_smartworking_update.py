# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""
a caribou migration

name: smartworking_update
version: 20261028121900
"""


def upgrade(connection):
    sql = """
        UPDATE `gm_timetable_type_data_area`
            SET `temp_id` = 2
        WHERE `id` IN (222, 282);
    """
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    pass
