#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C)2018-19 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
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

# ROOM NAME
HOMPI_ID = 'Living'
# HOMPI_SERVERS = ['http://hompi2_ip:5000','http://hompi3_ip:5000',]
HOMPI_SERVERS = []

# ENABLED MODULES
MODULE_TEMP = True
MODULE_METEO = True
MODULE_APHORISM = True
MODULE_DB_LOG = True
MODULE_SPEECH = False
MODULE_AMBIENT = False

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
BUTTON_DURATION_SECS = 3

# AMBIENT LED
LED_RIGHT_TO_LEFT = False

# DEBUGGING
TEST_MODE = 1
VERBOSE_LOG = False

# VARIOUS SETTINGS
HEATING_THRESHOLD = .05
TEMP_CORRECTION = 1.036
THERMO_CHANGE_MINS = 5
PLACE = 'milan'
IMAGE_PATH = './res/images/*.jpg'
THUMB_SIZE = (800, 800)
HOLIDAYS_COUNTRY = "IT"

# SPEECH
SPEECH_COMMAND = 'espeak -vit+m3 -s150 -k10 "{}"'

# AMBIENT COMMANDS
AMBIENT_INIT_COMMAND = 'clear'
AMBIENT_SETCOLOR_COMMAND = 'set_color {}'
AMBIENT_CROSSFADE_COMMAND = 'crossfade {} {}'
AMBIENT_GOING_TO_SLEEP_COMMAND = 'going_to_sleep {}'
AMBIENT_ACK_COMMAND = 'curtain_in_out {} {}'
AMBIENT_XMAS_DAISY_COMMAND = 'xmas_daisy {} {}'
AMBIENT_TRANSITION_FRAMES = 100

# TELEGRAM INTEGRATION
ENABLE_TELEGRAM = False

# API PRE-SHARED KEY
API_KEY = 'change-me'
