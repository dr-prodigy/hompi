import os
"""
a caribou migration

name: trv_tuning5
version: 20241107195500
"""


def upgrade(connection):
    scriptFile = open(os.path.dirname(os.path.realpath(__file__)) + "/20241107195500_trv_tuning5.sql", 'r')
    script = scriptFile.read()
    scriptFile.close()
    connection.executescript(script)

    connection.commit()

def downgrade(connection):
    pass
