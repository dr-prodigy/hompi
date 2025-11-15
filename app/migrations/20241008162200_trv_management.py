"""
a caribou migration

name: trv_management
version: 20241008162200
"""


def upgrade(connection):
    sql = """
        CREATE TABLE `gm_area` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `area_name` TEXT NOT NULL,
            `mqtt_temp_name` TEXT NOT NULL,
            `mqtt_cur_temp_c_regex` TEXT NOT NULL, 
            `mqtt_req_temp_c_regex` TEXT, 
            `temp_calibration` INTEGER NOT NULL DEFAULT 0,
            `mqtt_trv_name` TEXT,
            `mqtt_trv_publish_payload` TEXT )
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        CREATE TABLE `gm_timetable_type_data_area` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `timetable_type_data_id` INTEGER NOT NULL,
            `area_id` INTEGER,
            `temp_id` INTEGER NOT NULL,
            FOREIGN KEY(`timetable_type_data_id`) REFERENCES `gm_timetable_type_data`(`id`),
            FOREIGN KEY(`area_id`) REFERENCES `gm_area`(`id`),
            FOREIGN KEY(`temp_id`) REFERENCES `gm_temp`(`id`) )
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_area`
            (`id`, `area_name`, `mqtt_temp_name`, `mqtt_cur_temp_c_regex`, `mqtt_req_temp_c_regex`,
             `temp_calibration`, `mqtt_trv_name`, `mqtt_trv_publish_payload`)
        VALUES (1, 'test-area', 'test-temp', '{myregex}', '{myregex}',0,
        'test-trv', '{"boost_heating": "OFF", "child_lock": "UNLOCK", "current_heating_setpoint": **TEMP**, "eco_mode": "OFF", "eco_temperature": 19, "local_temperature_calibration": **TEMP_CAL**, "preset": "manual", "window_detection": "OFF"}')
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_timetable_type_data_area`
            (`timetable_type_data_id`, `area_id`, `temp_id`)
        VALUES (4, null, 1)
    """
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    pass