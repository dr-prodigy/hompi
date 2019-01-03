"""
a caribou migration

name: gm_timetable_day_type 
version: 20190103223309
"""

def upgrade(connection):
    sql = "CREATE TABLE `gm_timetable_type_data_temp` AS SELECT * FROM `gm_timetable_type_data`"
    connection.execute(sql)
    connection.commit()

    sql = "DROP TABLE `gm_timetable_type_data`"
    connection.execute(sql)
    connection.commit()

    sql = """
        CREATE TABLE `gm_timetable_type_data` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `orderby` INTEGER,
            `day_type_id` INTEGER NOT NULL,
            `temp_id` INTEGER NOT NULL,
            `time_hhmm` INTEGER NOT NULL,
            `delta_calc_mm` INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(`day_type_id`) REFERENCES `gm_timetable_day_type`(`id`),
            FOREIGN KEY(`temp_id`) REFERENCES `gm_temp`(`id`) )
    """
    connection.execute(sql)
    connection.commit()

    sql = "INSERT INTO `gm_timetable_type_data` SELECT * FROM `gm_timetable_type_data_temp`"
    connection.execute(sql)
    connection.commit()

    sql = "DROP TABLE `gm_timetable_type_data_temp`"
    connection.execute(sql)
    connection.commit()

    
def downgrade(connection):
    # add your downgrade step here
    pass
