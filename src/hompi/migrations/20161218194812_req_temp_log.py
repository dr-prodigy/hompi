"""
a caribou migration

name: io_management
version: 20161218194812
"""

def upgrade(connection):
    sql = """
        ALTER TABLE `gm_log`
            ADD COLUMN `req_temp_c`    REAL
        """
    connection.execute(sql)

    sql = """UPDATE `gm_log` SET `req_temp_c` = `int_temp_c` - 1.0"""
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    sql = "ALTER TABLE `gm_log` RENAME TO `gm_log_old`"
    connection.execute(sql)
    connection.commit()

    sql = """
        CREATE TABLE `gm_log` (
            `id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            `datetime`	INTEGER NOT NULL,
            `int_temp_c`	REAL NOT NULL,
            `ext_temp_c`	REAL,
            `event`	TEXT,
            `description`	TEXT
        )
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_log`
            (`id`, `datetime`, `int_temp_c`, `ext_temp_c`, `event`, `description`)
        SELECT 
            `id`, `datetime`, `int_temp_c`, `ext_temp_c`, `event`, `description`
        FROM `gm_log_old`
    """
    connection.execute(sql)
    connection.commit()

    sql = "DROP TABLE `gm_log_old`"
    connection.execute(sql)
    connection.commit()


