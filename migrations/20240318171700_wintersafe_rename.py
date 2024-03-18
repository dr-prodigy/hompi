"""
a caribou migration

name: wintersafe_rename
version: 20240318171700
"""


def upgrade(connection):
    sql = "UPDATE `gm_temp` SET description = 'Winter_safe' WHERE description = 'Winter-safe';"
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    sql = "UPDATE `gm_temp` SET description = 'Winter-safe' WHERE description = 'Winter_safe';"
    connection.execute(sql)
    connection.commit()
