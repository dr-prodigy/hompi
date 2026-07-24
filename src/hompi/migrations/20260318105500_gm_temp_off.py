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
