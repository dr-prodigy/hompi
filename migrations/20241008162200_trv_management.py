"""
a caribou migration

name: trv_management
version: 20241008162200
"""


def upgrade(connection):
    sql = """
        CREATE TABLE `gm_trv` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `friendly_name` TEXT NOT NULL,
            `calibration` INTEGER NOT NULL DEFAULT 0 )
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        CREATE TABLE `gm_timetable_type_data_trv` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `timetable_type_data_id` INTEGER NOT NULL,
            `trv_id` INTEGER,
            `temp_id` INTEGER NOT NULL,
            FOREIGN KEY(`timetable_type_data_id`) REFERENCES `gm_timetable_type_data`(`id`),
            FOREIGN KEY(`trv_id`) REFERENCES `gm_trv`(`id`),
            FOREIGN KEY(`temp_id`) REFERENCES `gm_temp`(`id`) )
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_trv`
            (`id`, `friendly_name`, `calibration`)
        VALUES (1, 'test-trv', -2)
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_timetable_type_data_trv`
            (`timetable_type_data_id`, `trv_id`, `temp_id`)
        VALUES (4, null, 1)
    """
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    pass