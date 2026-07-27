# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""
a caribou migration

name: gm_timetable_holidays 
version: 20180121171238
"""

def upgrade(connection):
    # add pre_holiday and holiday columns
    sql = """
        ALTER TABLE `gm_timetable` ADD COLUMN `pre_holiday` INTEGER
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        ALTER TABLE `gm_timetable` ADD COLUMN `holiday` INTEGER
    """
    connection.execute(sql)
    connection.commit()

    # default them to saturday and sunday programs
    sql = """
        UPDATE `gm_timetable` SET `pre_holiday` = `saturday`, `holiday` = `sunday`
    """
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    sql = "ALTER TABLE `gm_timetable` RENAME TO `gm_timetable_old`"
    connection.execute(sql)
    connection.commit()

    sql = """
        CREATE TABLE `gm_timetable` (
            `id`	INTEGER PRIMARY KEY AUTOINCREMENT,
            `description`	TEXT NOT NULL,
            `monday`	INTEGER,
            `tuesday`	INTEGER,
            `wednesday`	INTEGER,
            `thursday`	INTEGER,
            `friday`	INTEGER,
            `saturday`	INTEGER,
            `sunday`	INTEGER,
            `short_description` TEXT
        )
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_timetable`
            (`id`, `description`, `monday`, `tuesday`, `wednesday`,`thursday`, `friday`, `saturday`, `sunday`,
            `short_description`)
        SELECT 
            `id`, `description`, `monday`, `tuesday`, `wednesday`,`thursday`, `friday`, `saturday`, `sunday`,
            `short_description`
        FROM `gm_timetable_old`
    """
    connection.execute(sql)
    connection.commit()

    sql = "DROP TABLE `gm_timetable_old`"
    connection.execute(sql)
    connection.commit()
