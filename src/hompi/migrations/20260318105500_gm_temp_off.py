# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""
a caribou migration

name: gm_temp_off
version: 20260318105500
"""


def upgrade(connection):
    sql = """
        UPDATE `gm_temp`
            SET `temp_c` = 0
        WHERE `id` = 5;
    """
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    pass
