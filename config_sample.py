#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C)2018-24 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>.
#
# hompi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# hompi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with hompi.  If not, see <http://www.gnu.org/licenses/>.

# **** Copy me to config.py and modify me as needed ****

from utils import LOG_DEBUG, LOG_INFO, LOG_WARN, LOG_ERROR

# ROOM NAME
HOMPI_ID = 'Living'
# HOMPI_SERVERS = ['http://hompi2_ip:5000','http://hompi3_ip:5000',]
HOMPI_SERVERS = []
HOMPI_EXT_SENSORS = []

# ENABLED MODULES
MODULE_TEMP = True
MODULE_METEO = True
MODULE_APHORISM = True
MODULE_DB_LOG = False
MODULE_SPEECH = False
MODULE_AMBIENT = False

# TELEGRAM INTEGRATION
ENABLE_TELEGRAM = False

# HASS INTEGRATION
ENABLE_HASS_INTEGRATION = True
HASS_SERVER = 'http://localhost:8123/'
HASS_CHECK_SSL_CERT = False
HASS_TOKEN = 'abc123'

# TRV INTEGRATION
ENABLE_TRV_INTEGRATION = True
MQTT_BROKER = 'localhost'
MQTT_PORT = 1883
MQTT_BASE_TOPIC = 'zigbee2mqtt'
TRV_DATA_EXPIRATION_SECS = 3600 # 1 hour

# LCD modes : NONE = 0, GPIO_CharLCD = 1, I2C = 2
MODULE_LCD = 2
I2C_BUS = 1  # i2c bus (0 -- original Pi, 1 -- Rev 2 Pi)
I2C_ADDRESS = 0x27
LCD_COLUMNS = 16
LCD_ROWS = 2

# RELAY MODE
RELAY_HILOW_MODE = False

# HEATING RELAY
HEATING_GPIO = 17

# PUSH-BUTTON RELAYS (GPIO, NAME)
BUTTONS = [
    [18, 'Gate'],
    [22, 'Living'],
    [23, 'Bedroom'],
]
BUTTON_DURATION_SECS = 1

# AMBIENT LED
LED_RIGHT_TO_LEFT = False

# DEBUGGING
TEST_MODE = 1
LOG_LEVEL = LOG_DEBUG
LOG_MUTE_MODULES = []

# VARIOUS SETTINGS
HEATING_THRESHOLD = .1
TEMP_CORRECTION = 1.036
THERMO_CHANGE_MINS = 5
PLACE = 'milan'
IMAGE_PATH = './res/images/*.jpg'
THUMB_SIZE = (800, 800)
HOLIDAYS_COUNTRY = "IT"
LCD_SKIP_EXTRA_INFO = True

# SPEECH
SPEECH_COMMAND = 'espeak -vit+m3 -s150 -k10 "{}"'

# AMBIENT
AMBIENT_TRANSITION_FRAMES = 100

# API PRE-SHARED KEY
# API_KEY = 'change-me'
