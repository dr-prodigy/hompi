import os
"""
a caribou migration

name: trv_disable
version: 20241219193000
"""


def upgrade(connection):
    sql = "ALTER TABLE `gm_area` ADD `enabled` INTEGER NOT NULL DEFAULT 1"
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    pass
