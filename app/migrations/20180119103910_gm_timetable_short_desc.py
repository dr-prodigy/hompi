"""
a caribou migration

name: gm_timetable_short_desc 
version: 20180119103910
"""

def upgrade(connection):
    sql = """
        ALTER TABLE `gm_timetable` ADD COLUMN short_description TEXT
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        UPDATE `gm_timetable` SET short_description = SUBSTR(description, 1,1)
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
            `sunday`	INTEGER
        )
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_timetable`
            (`id`, `description`, `monday`, `tuesday`, `wednesday`,`thursday`, `friday`, `saturday`, `sunday`)
        SELECT 
            `id`, `description`, `monday`, `tuesday`, `wednesday`,`thursday`, `friday`, `saturday`, `sunday`
        FROM `gm_timetable_old`
    """
    connection.execute(sql)
    connection.commit()

    sql = "DROP TABLE `gm_timetable_old`"
    connection.execute(sql)
    connection.commit()
