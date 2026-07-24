import os
"""
a caribou migration

name: trv_tuning
version: 20241020101100
"""


def upgrade(connection):
    # - removed child_lock setting ( = allow HA control)
    # - default to window detection
    sql = """
        UPDATE `gm_area`
        SET
            `mqtt_trv_publish_payload` = '{"boost_heating": "OFF", "current_heating_setpoint": **TEMP**, "eco_mode": "OFF", "local_temperature_calibration": **TEMP_CAL**, "preset": "manual", "window_detection": "ON"}'
        WHERE
            `id` IN (1,2,3,4)
    """
    connection.execute(sql)
    connection.commit()

def downgrade(connection):
    pass
