"""
a caribou migration

name: trv_init_data
version: 20241016224800
"""


def upgrade(connection):
    sql = """
        UPDATE `gm_timetable_type_data`
        SET `time_hhmm` = 2030
        WHERE `id` = 16
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_timetable_type_data` (`id`, `orderby`, `day_type_id`, `temp_id`, `time_hhmm`, `delta_calc_mm`)
        VALUES (17, 3, 7, 2, 2330, 0)
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        DELETE FROM `gm_area`
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_area`
            (`id`, `area_name`, `mqtt_temp_name`, `mqtt_temp_payload_regex`, `temp_calibration`,
             `mqtt_trv_name`, `mqtt_trv_publish_payload`)
        VALUES (1, 'Cucina', 'TRV1', '"local_temperature": *([0-9.-]*),', 0,
        'TRV1', '{"boost_heating": "OFF", "child_lock": "UNLOCK", "current_heating_setpoint": **TEMP**, "eco_mode": "OFF", "local_temperature_calibration": **TEMP_CAL**, "preset": "manual", "window_detection": "OFF"}')
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_area`
            (`id`, `area_name`, `mqtt_temp_name`, `mqtt_temp_payload_regex`, `temp_calibration`,
             `mqtt_trv_name`, `mqtt_trv_publish_payload`)
        VALUES (2, 'Bagnetto', 'TRV2', '"local_temperature": *([0-9.-]*),', 0,
        'TRV2', '{"boost_heating": "OFF", "child_lock": "UNLOCK", "current_heating_setpoint": **TEMP**, "eco_mode": "OFF", "local_temperature_calibration": **TEMP_CAL**, "preset": "manual", "window_detection": "OFF"}')
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_area`
            (`id`, `area_name`, `mqtt_temp_name`, `mqtt_temp_payload_regex`, `temp_calibration`,
             `mqtt_trv_name`, `mqtt_trv_publish_payload`)
        VALUES (3, 'Camera', 'TRV3', '"local_temperature": *([0-9.-]*),', -3,
        'TRV3', '{"boost_heating": "OFF", "child_lock": "UNLOCK", "current_heating_setpoint": **TEMP**, "eco_mode": "OFF", "local_temperature_calibration": **TEMP_CAL**, "preset": "manual", "window_detection": "OFF"}')
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_area`
            (`id`, `area_name`, `mqtt_temp_name`, `mqtt_temp_payload_regex`, `temp_calibration`,
             `mqtt_trv_name`, `mqtt_trv_publish_payload`)
        VALUES (4, 'Cameretta', 'TRV4', '"local_temperature": *([0-9.-]*),', 0,
        'TRV4', '{"boost_heating": "OFF", "child_lock": "UNLOCK", "current_heating_setpoint": **TEMP**, "eco_mode": "OFF", "local_temperature_calibration": **TEMP_CAL**, "preset": "manual", "window_detection": "OFF"}')
    """
    connection.execute(sql)
    connection.commit()

    sql = """
        INSERT INTO `gm_area`
            (`id`, `area_name`, `mqtt_temp_name`, `mqtt_temp_payload_regex`, `temp_calibration`,
             `mqtt_trv_name`, `mqtt_trv_publish_payload`)
        VALUES (5, 'Bagno', 'TempHum1_S', '""temperature": *([0-9.-]*),', 0,
        '', '')
    """
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    pass
