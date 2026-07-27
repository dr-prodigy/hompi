# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""
a caribou migration

name: trv_add_data
version: 20250129192600
"""


def upgrade(connection):
    sql = """
        UPDATE `gm_area`
            SET `mqtt_temp_name` = 'TempCameretta_S',
            `mqtt_cur_temp_c_regex` = '"temperature": *([0-9.-]*)',
            `mqtt_req_temp_c_regex` = NULL,
            `mqtt_trv_name` = NULL,
            `enabled` = 1
        WHERE `id` = 4;
    """
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    pass
