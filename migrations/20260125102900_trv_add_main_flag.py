"""
a caribou migration

name: trv_add_main_flag
version: 20260125102900
"""


def upgrade(connection):
    sql = """
        ALTER TABLE `gm_control` ADD COLUMN `main_area_id` INTEGER DEFAULT 0
        REFERENCES `gm_area`(`id`)
    """
    connection.execute(sql)
    connection.commit()

    sql = "UPDATE `gm_control` SET `main_area_id` = 2"
    connection.execute(sql)
    connection.commit()


def downgrade(connection):
    pass
