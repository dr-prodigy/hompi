"""
a caribou migration

name: io_management
version: 20161126174842
"""

def upgrade(connection):
    sql = """
        CREATE TABLE `gm_output` (
        `id`	INTEGER NOT NULL PRIMARY KEY DEFAULT 0,
        `last_update`	INTEGER NOT NULL DEFAULT (strftime('%s','now')),
        `data`	TEXT
        )"""
    connection.execute(sql)

    sql = """INSERT INTO `gm_output` (`id`,`data`) VALUES (0,null)"""
    connection.execute(sql)
    connection.commit()

    sql = """
        CREATE TABLE `gm_input` (
        `id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        `last_update`	INTEGER NOT NULL DEFAULT (strftime('%s','now')),
        `data`	TEXT
        )"""
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    sql = "DROP TABLE `gm_output`"
    connection.execute(sql)
    sql = "DROP TABLE `gm_input`"
    connection.execute(sql)
    connection.commit()
