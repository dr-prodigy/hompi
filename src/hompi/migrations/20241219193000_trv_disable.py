# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

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
