import os
"""
a caribou migration

name: trv_tuning3
version: 20241028120300
"""


def upgrade(connection):
    sql = """
        UPDATE `gm_area`
        SET
            `mqtt_trv_publish_payload` = '{"current_heating_setpoint": **TEMP**, "local_temperature_calibration": **TEMP_CAL**, "preset": "manual", "window_detection": "ON", "boost_heating": "OFF", "eco_mode": "OFF", "programming_mode":
"06:00/20°C  12:00/21°C  14:30/20°C  22:00/18°C  06:00/20°C  12:00/21°C  14:30/20°C  22:00/18°C  06:00/20°C  12:00/21°C  14:30/20°C  22:00/18°C"}'
        WHERE
            `id` IN (1,2,3,4)
    """
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    pass
