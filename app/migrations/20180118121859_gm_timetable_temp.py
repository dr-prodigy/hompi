"""
a caribou migration

name: gm_timetable_temp 
version: 20180118121859
"""

def upgrade(connection):
    sql = """
        CREATE TABLE `gm_timetable_temp` (
            `id`	INTEGER PRIMARY KEY AUTOINCREMENT,
            `timetable_id`	INTEGER,
            `temp_id`	INTEGER,
            FOREIGN KEY(`timetable_id`) REFERENCES `gm_timetable`(`id`),
            FOREIGN KEY(`temp_id`) REFERENCES `gm_temp`(`id`)
        )
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_timetable_temp`  (`timetable_id`, `temp_id`)
        SELECT `timetable_id`, `id` FROM `gm_temp`
    """
    connection.execute(sql)
    connection.commit()

    sql = "ALTER TABLE `gm_temp` RENAME TO `gm_temp_old`"
    connection.execute(sql)
    connection.commit()

    sql = """
        CREATE TABLE `gm_temp` (
            `id`	INTEGER PRIMARY KEY AUTOINCREMENT,
            `description`	TEXT,
            `temp_c`	REAL NOT NULL)
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_temp` (`id`, `description`, `temp_c`)
        SELECT `id`, `description`, `temp_c` FROM `gm_temp_old`
    """
    connection.execute(sql)
    connection.commit()

    sql = "DROP TABLE `gm_temp_old`"
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    sql = "ALTER TABLE `gm_temp` ADD COLUMN `timetable_id` INTEGER"
    connection.execute(sql)
    connection.commit()

    sql = """
        UPDATE `gm_temp` SET `timetable_id` = 
        (SELECT MIN(timetable_id) FROM `gm_timetable_temp`
        WHERE `temp_id` = `gm_temp`.`id`)
        WHERE EXISTS
        (SELECT * FROM `gm_timetable_temp`
        WHERE `temp_id` = `gm_temp`.`id`)
    """
    connection.execute(sql)
    connection.commit()

    sql = "DROP TABLE `gm_timetable_temp`"
    connection.execute(sql)
    connection.commit()