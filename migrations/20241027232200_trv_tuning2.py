import os
"""
a caribou migration

name: trv_tuning2
version: 20241022232200
"""


def upgrade(connection):
    scriptFile = open(os.path.dirname(os.path.realpath(__file__)) + "/20241027222300_trv_tuning2.sql", 'r')
    script = scriptFile.read()
    scriptFile.close()
    connection.executescript(script)

    connection.commit()

def downgrade(connection):
    pass
