import os
"""
a caribou migration

name: trv_add_data
version: 20241017230200
"""


def upgrade(connection):
    sql = """
        UPDATE `gm_timetable_type_data`
        SET `id`=`id`+1,`orderby`=`orderby`+1
        WHERE `id` = 17
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        UPDATE `gm_timetable_type_data`
        SET `id`=`id`+1,`orderby`=`orderby`+1
        WHERE `id` = 16
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_timetable_type_data` (`id`, `orderby`, `day_type_id`, `temp_id`, `time_hhmm`, `delta_calc_mm`)
        VALUES (16, 2, 7, 3, 830, 0)
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        UPDATE `gm_area`
        SET `area_name` = 'Soggiorno'
        WHERE `id` = 2
    """
    connection.execute(sql)
    connection.commit()

    sql = "DELETE FROM `gm_timetable_type_data_area`"
    connection.execute(sql)
    connection.commit()

    scriptFile = open(os.path.dirname(os.path.realpath(__file__)) + "/20241017230200_trv_add_data.sql", 'r')
    script = scriptFile.read()
    scriptFile.close()
    connection.executescript(script)

    connection.commit()

def downgrade(connection):
    pass
