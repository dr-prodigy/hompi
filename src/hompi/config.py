# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""Load Hompi settings from a YAML file.

Usage::

    from hompi.config import config
    print(config.HOMPI_ID)

The settings object exposes the same uppercase attribute names as the former
``config.py`` module.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from ._path import ensure_runtime_paths, find_config_file

# Log level constants (kept for callers that historically read them from config)
LOG_GPIO = 0
LOG_DEBUG = 1
LOG_INFO = 2
LOG_WARN = 3
LOG_ERROR = 4

_DEFAULTS = {
    'TMPFS_ENABLE': True,
    'TMPFS_PATH': '/tmp/',
    'HOMPI_ID': 'Living',
    'HOMPI_SERVERS': [],
    'HOMPI_EXT_SENSORS': [],
    'MODULE_METEO': True,
    'MODULE_APHORISM': True,
    'APHORISM_KEY': None,
    'MODULE_DB_LOG': False,
    'MODULE_SPEECH': False,
    'MODULE_AMBIENT': False,
    'ENABLE_TELEGRAM': False,
    'MODULE_HASS': True,
    'HASS_SERVER': 'http://localhost:8123/',
    'HASS_CHECK_SSL_CERT': False,
    'HASS_TOKEN': 'abc123',
    'MODULE_TEMP': True,
    'MODULE_HEATING': True,
    'MODULE_TRV': True,
    'MQTT_BROKER': 'localhost',
    'MQTT_PORT': 1883,
    'MQTT_BASE_TOPIC': 'zigbee2mqtt',
    'TRV_DATA_EXPIRATION_SECS': 3600,
    'TRV_KEEPALIVE': True,
    'THERMOSTAT_MODE': 3,
    'MODULE_LCD': 2,
    'I2C_BUS': 1,
    'I2C_ADDRESS': 0x27,
    'LCD_COLUMNS': 16,
    'LCD_ROWS': 2,
    'LCD_SKIP_EXTRA_INFO': True,
    'RELAY_HILOW_MODE': False,
    'HEATING_GPIO': 17,
    'BUTTONS': [
        [18, 'Gate'],
        [22, 'Living'],
        [23, 'Bedroom'],
    ],
    'BUTTON_DURATION_SECS': 1,
    'LED_RIGHT_TO_LEFT': False,
    'AMBIENT_TRANSITION_FRAMES': 100,
    'TEST_MODE': 1,
    'LOG_LEVEL': LOG_DEBUG,
    'LOG_MUTE_MODULES': [],
    'HW_LOG': False,
    'HEATING_THRESHOLD': 0.1,
    'TEMP_CORRECTION': 0,
    'THERMO_CHANGE_MINS': 5,
    'PLACE': 'milan',
    'IMAGE_PATH': './res/images/*.jpg',  # resolved under HOMPI_HOME / data dir
    'THUMB_SIZE': [800, 800],
    'HOLIDAYS_COUNTRY': 'IT',
    'SPEECH_COMMAND': 'espeak -vit+m3 -s150 -k10 "{}"',
    'API_KEY': None,
    # Mirror former config.py constants for utils.py compatibility
    'LOG_GPIO': LOG_GPIO,
    'LOG_DEBUG': LOG_DEBUG,
    'LOG_INFO': LOG_INFO,
    'LOG_WARN': LOG_WARN,
    'LOG_ERROR': LOG_ERROR,
}


class Settings:
    """Attribute-style access to configuration values."""

    def __init__(self, values):
        self._values = dict(values)
        self._config_path = None

    def __getattr__(self, name):
        try:
            return self._values[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        if name in ('_values', '_config_path'):
            object.__setattr__(self, name, value)
        else:
            self._values[name] = value

    def get(self, name, default=None):
        return self._values.get(name, default)

    def as_dict(self):
        return dict(self._values)


def _coerce(values):
    data = dict(_DEFAULTS)
    if not values:
        return data
    data.update(values)
    # Normalize types that YAML may leave ambiguous
    if isinstance(data.get('THUMB_SIZE'), list):
        data['THUMB_SIZE'] = tuple(data['THUMB_SIZE'])
    if data.get('BUTTONS') is None:
        data['BUTTONS'] = []
    if data.get('LOG_MUTE_MODULES') is None:
        data['LOG_MUTE_MODULES'] = []
    if data.get('HOMPI_SERVERS') is None:
        data['HOMPI_SERVERS'] = []
    if data.get('HOMPI_EXT_SENSORS') is None:
        data['HOMPI_EXT_SENSORS'] = []
    # Empty string API key → treat as unset
    if data.get('API_KEY') == '':
        data['API_KEY'] = None
    return data


def load_settings(path=None):
    """Load settings from YAML. ``path`` overrides discovery."""
    ensure_runtime_paths()
    config_path = Path(path) if path else find_config_file()
    if config_path is None:
        raise FileNotFoundError(
            'No Hompi config found. Copy config.sample.yaml to config.yaml '
            'or set HOMPI_CONFIG to a YAML file path.'
        )
    with open(config_path, encoding='utf-8') as fh:
        raw = yaml.safe_load(fh) or {}
    if not isinstance(raw, dict):
        raise ValueError(f'Config root must be a mapping: {config_path}')
    settings = Settings(_coerce(raw))
    settings._config_path = str(config_path)
    return settings


# Eager singleton used by the rest of the package
config = load_settings()
