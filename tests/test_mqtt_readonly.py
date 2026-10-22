# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""MQTT_READONLY skips device publishes while leaving subscribe paths intact."""

from unittest.mock import MagicMock

from hompi import mqtt as mqtt_mod
from hompi.config import config


def test_publish_skipped_when_mqtt_readonly(monkeypatch):
    monkeypatch.setattr(config, 'MQTT_READONLY', True)
    monkeypatch.setattr(config, 'MQTT_BASE_TOPIC', 'zigbee2mqtt')

    client = mqtt_mod.MQTT(io_status=MagicMock())
    client._MQTT__connected = True
    client._MQTT__client = MagicMock()
    client._MQTT__areas[1] = {
        'area_name': 'Soggiorno',
        'mqtt_trv_name': 'TRV1',
        'mqtt_trv_publish_payload': (
            '{"current_heating_setpoint": **TEMP**, '
            '"local_temperature_calibration": **TEMP_CAL**}'
        ),
    }

    published = client._MQTT__publish(1, 22.5, -1.0)

    assert published is True
    client._MQTT__client.publish.assert_not_called()


def test_publish_calls_client_when_not_readonly(monkeypatch):
    monkeypatch.setattr(config, 'MQTT_READONLY', False)
    monkeypatch.setattr(config, 'MQTT_BASE_TOPIC', 'zigbee2mqtt')

    mock_result = MagicMock()
    mock_result.is_published.return_value = True
    mock_client = MagicMock()
    mock_client.publish.return_value = mock_result

    client = mqtt_mod.MQTT(io_status=MagicMock())
    client._MQTT__connected = True
    client._MQTT__client = mock_client
    client._MQTT__areas[1] = {
        'area_name': 'Soggiorno',
        'mqtt_trv_name': 'TRV1',
        'mqtt_trv_publish_payload': (
            '{"current_heating_setpoint": **TEMP**, '
            '"local_temperature_calibration": **TEMP_CAL**}'
        ),
    }

    published = client._MQTT__publish(1, 22.5, -1.0)

    assert published is True
    mock_client.publish.assert_called_once_with(
        'zigbee2mqtt/TRV1/set',
        '{"current_heating_setpoint": 22, '
        '"local_temperature_calibration": -1}',
    )
