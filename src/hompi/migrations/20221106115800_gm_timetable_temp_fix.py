# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""
a caribou migration

name: gm_timetable_temp_fix
version: 20221106115800
"""

def upgrade(connection):
    sql = "PRAGMA foreign_keys=off;"
    connection.execute(sql)
    connection.commit()

    sql = "ALTER TABLE `gm_timetable_temp` RENAME TO `gm_timetable_temp_old`"
    connection.execute(sql)
    connection.commit()

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

    sql = "INSERT INTO `gm_timetable_temp` SELECT * FROM `gm_timetable_temp_old`"
    connection.execute(sql)
    connection.commit()

    sql = "DROP TABLE `gm_timetable_temp_old`"
    connection.execute(sql)
    connection.commit()

    sql = "PRAGMA foreign_keys=on"
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    # add your downgrade step here
    pass
