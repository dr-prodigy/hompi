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

import sys
import datetime
import traceback
import math
from time import strftime

import config

from utils import log_stderr

NONE = 0
GPIO_CharLCD = 1
I2C_LCD = 2

DISPLAY_TYPE = NONE
PAUSED = False

try:
    DISPLAY_TYPE = config.MODULE_LCD
except Exception:
    pass

if DISPLAY_TYPE == GPIO_CharLCD:
    from lib.RPiGPIO_CharLCD import RPiGPIO_CharLCD
elif DISPLAY_TYPE == I2C_LCD:
    from lib import I2C_LCD_driver
else:
    DISPLAY_TYPE = NONE

# charsets
CHARSET_SYMBOL = 0
CHARSET_BIGNUM = 1

CURRENT_CHARSET = None
# NEW_CHARSET = CHARSET_SYMBOL # change charset
NEW_CHARSET = CHARSET_BIGNUM

# RPiGPIO_CharLCD pin configuration:
LCD_RS = 27  # Note this might need to be changed to 21 for older revision Pi's
LCD_EN = 22
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 18
LCD_BACKLIGHT = 4  # NOT USED

# I2C_LCD configuration
# i2c bus (0 -- original Pi, 1 -- Rev 2 Pi)
try:
    I2C_BUS = config.I2C_BUS
except Exception:
    I2C_BUS = 1
# LCD Address (0X27 = 16x2)
try:
    I2C_ADDRESS = config.I2C_ADDRESS
except Exception:
    I2C_ADDRESS = 0x27
# LCD COLUMNS
try:
    LCD_COLUMNS = config.LCD_COLUMNS
except Exception:
    LCD_COLUMNS = 16
# LCD COLUMNS
try:
    LCD_ROWS = config.LCD_ROWS
except Exception:
    LCD_ROWS = 2

# global parameters
LCD_LINE_DELAY = 3

SYMBOLDATA = [
    # on icon (flame) /x00
    [0b01000,
     0b01001,
     0b00110,
     0b01011,
     0b10101,
     0b10101,
     0b01110,
     0b00000],
    # warming icon (empty flame) /x01
    [0b01000,
     0b01001,
     0b00110,
     0b01001,
     0b10001,
     0b10001,
     0b01110,
     0b00000],
    # cooling icon (smokey) /x02
    [0b00000,
     0b00100,
     0b01000,
     0b00100,
     0b00010,
     0b00100,
     0b11111,
     0b00000],
    # automatic char /x03
    [0b00000,
     0b00000,
     0b01110,
     0b10101,
     0b10111,
     0b10001,
     0b01110,
     0b00000],
    # manual char /x04
    [0b00100,
     0b01110,
     0b11110,
     0b11111,
     0b10001,
     0b10001,
     0b10001,
     0b10010]
]

BIGNUMDATA = [
    # on icon (flame) /x00
    [0b01000,
     0b01001,
     0b00110,
     0b01011,
     0b10111,
     0b10101,
     0b01110,
     0b00000],
    # warming icon (empty flame) /x01
    [0b01000,
     0b01001,
     0b00110,
     0b01001,
     0b10001,
     0b10001,
     0b01110,
     0b00000],
    # cooling icon (smokey) /x02
    [0b01000,
     0b10000,
     0b01000,
     0b10101,
     0b10101,
     0b10101,
     0b10101,
     0b00000],
    # automatic char /x03
    [0b00000,
     0b00000,
     0b01110,
     0b10101,
     0b10111,
     0b10001,
     0b01110,
     0b00000],
    # manual char /x04
    [0b00100,
     0b01110,
     0b11110,
     0b11111,
     0b10001,
     0b10001,
     0b10001,
     0b10010],
    # up \x05
    [0b11111,
     0b11111,
     0b11111,
     0b00000,
     0b00000,
     0b00000,
     0b00000,
     0b00000],
    # down \x06
    [0b00000,
     0b00000,
     0b00000,
     0b00000,
     0b00000,
     0b11111,
     0b11111,
     0b11111],
    # up+down \x07
    [0b11111,
     0b11111,
     0b11111,
     0b00000,
     0b00000,
     0b11111,
     0b11111,
     0b11111]
]
BIGNUMMATRIX = {
    '0': ['\xFF\x05\xFF ',
          '\xFF\x06\xFF '],
    '1': ['\x06\xFF ',
          ' \xFF '],
    '2': ['\x05\x07\xFF ',
          '\xFF\x06\x06 '],
    '3': ['\x05\x07\xFF ',
          '\x06\x06\xFF '],
    '4': ['\xFF\x06\xFF ',
          '  \xFF '],
    '5': ['\xFF\x07\x05 ',
          '\x06\x06\xFF '],
    '6': ['\xFF\x07\x07 ',
          '\xFF\x06\xFF '],
    '7': ['\x05\x05\xFF ',
          ' \xFF  '],
    '8': ['\xFF\x07\xFF ',
          '\xFF\x06\xFF '],
    '9': ['\xFF\x07\xFF ',
          '\x06\x06\xFF '],
    ' ': [' ',
          ' '],
    '.': [' ',
          '.'],
    ':': ['\xA5',
          '\xA5'],
    '\'': ['\xDF',
           ' '],
}


class Dashboard:
    def __init__(self):
        self._current_program = -1
        self._is_backlit = True
        self._backlight_change = datetime.datetime(9999, 12, 31)
        self._command = ''
        self._message_timeout = datetime.datetime(9999, 12, 31)
        self.line = [''] * LCD_ROWS
        self.old_line = [''] * LCD_ROWS
        self.position = [-LCD_LINE_DELAY] * LCD_ROWS
        self.lcd = None
        self.refresh_display()

    def _load_charset(self):
        if PAUSED:
            return

        if CURRENT_CHARSET == CHARSET_SYMBOL:
            if DISPLAY_TYPE == GPIO_CharLCD:
                for font_count in range(0, 4):
                    self.lcd.create_char(font_count, SYMBOLDATA[font_count])
            elif DISPLAY_TYPE == I2C_LCD:
                self.lcd.lcd_load_custom_chars(SYMBOLDATA)
        elif CURRENT_CHARSET == CHARSET_BIGNUM:
            if DISPLAY_TYPE == GPIO_CharLCD:
                for font_count in range(0, 8):
                    self.lcd.create_char(font_count, BIGNUMDATA[font_count])
            elif DISPLAY_TYPE == I2C_LCD:
                self.lcd.lcd_load_custom_chars(BIGNUMDATA)

    def refresh_display(self, io_status = None):
        global PAUSED
        try:
            PAUSED = False
            if DISPLAY_TYPE == GPIO_CharLCD:
                # initialize display
                if self.lcd is None:
                    self.lcd = RPiGPIO_CharLCD(LCD_RS, LCD_EN, LCD_D4, LCD_D5,
                                               LCD_D6, LCD_D7,
                                               LCD_COLUMNS, LCD_ROWS,
                                               LCD_BACKLIGHT)
            elif DISPLAY_TYPE == I2C_LCD:
                # initialize display
                self.lcd = I2C_LCD_driver.lcd(I2C_ADDRESS, I2C_BUS)
            # load symbol font data
            self._load_charset()

            if io_status:
                # force lines refresh
                self.old_line = [''] * LCD_ROWS
                self.update(io_status)
        except KeyboardInterrupt:
            raise
        except Exception:
            log_stderr(traceback.format_exc())
            log_stderr('ERR: LCD init failed: PAUSED')
            PAUSED = True

    def set_charset(self, charset=CHARSET_SYMBOL):
        global NEW_CHARSET
        NEW_CHARSET = charset

    def change_dashboard_program(self, io_status):
        self._current_program = self._current_program + 1\
            if self._current_program < 12 else 0
        self.update(io_status)

    def update_content(self, io_status, change=True):
        if not config.MODULE_LCD or PAUSED:
            return

        # heating_simplified_icon = \
        #     '\x00' if io_status.heating_status == 'on' or \
        #     io_status.heating_status == 'warming' else '_'
        # mode_simplified_icon = io_status.short_mode_desc

        heating_icon = ' ' if io_status.short_mode_desc == 'O' else \
            '\x00' if io_status.heating_status == 'on' else \
            '\x01' if io_status.heating_status == 'warming' else \
            '\x02' if io_status.heating_status == 'cooling' else \
            '_'
        mode_icon = '\x03' if io_status.short_mode_desc == 'A' else \
            '\x04' if io_status.short_mode_desc == 'M' else \
            ' ' if io_status.short_mode_desc == 'O' else \
            io_status.short_mode_desc

        while True:
            # line2 additional modules
            if self._current_program in {3, 4, 7, 8, 11, 12}:
                if io_status.hompi_slaves or io_status.hompi_ext_sensors:
                    line2options = ''
                    for server_id, server_data in \
                            io_status.hompi_slaves.items():
                        line2options += '{} {:.1f}\xDFC'.format(
                            server_id,
                            server_data['int_temp_c'])
                    for sensor_id, sensor_data in \
                            io_status.hompi_ext_sensors.items():
                        line2options += '{} {:.1f}\xDFC'.format(
                            sensor_data['desc'],
                            sensor_data['temp'])
                    line2options = line2options.center(LCD_COLUMNS)
                    break
                else:
                    self._current_program += 2 if self._current_program < 11 \
                        else 1
                    continue

            if self._current_program in {5, 6} and not config.LCD_SKIP_EXTRA_INFO:
                if config.MODULE_METEO:
                    line2options = ('Ext. {:.1f}\xDFC - {:.0f}% ' +
                                    '- {:.0f}mb - {:.1f}m/s - {}').format(
                                    io_status.ext_temp_c, io_status.humidity,
                                    io_status.pressure, io_status.wind,
                                    io_status.weather)
                    break
                else:
                    self._current_program += 4
                    continue

            if self._current_program in {9, 10} and not config.LCD_SKIP_EXTRA_INFO:
                if config.MODULE_APHORISM:
                    line2options = '{} - {}'.format(
                        io_status.aphorism_text.encode('utf-8'),
                        io_status.aphorism_author.encode('utf-8'))
                    break
                else:
                    self._current_program = 1
                    continue

            # line2 default: heating status
            line2options = '{:.1f}\xDFC'.format(io_status.req_temp_c)
            if io_status.short_mode_desc == 'A':
                line2options = line2options.lstrip() +\
                               ' \x7E {:02.0f}:{:02.0f}'.format(
                                   math.floor(io_status.req_end_time // 100),
                                   io_status.req_end_time - math.floor(
                                       io_status.req_end_time // 100) * 100)
            elif io_status.short_mode_desc == 'O':
                line2options = 'OFF'
            elif io_status.short_mode_desc == 'W':
                line2options = 'Winter'
            if len(line2options) < LCD_COLUMNS - 3:
                line2options = line2options.center(LCD_COLUMNS)
            else:
                line2options = line2options.rjust(LCD_COLUMNS)
            line2options = '{} {}'.format(mode_icon, line2options[2:])
            break

        if config.TEST_MODE == 2:
            # bignum test mode
            main_temp = '0123456789\''
        else:
            if config.MODULE_TEMP and self._current_program % 4 == 0:
                main_temp = '{:04.1f}\''.format(io_status.int_temp_c)
            else:
                main_temp = strftime("%H:%M")

        main_temp1 = main_temp2 = ''
        for char in main_temp:
            try:
                if char == '.' \
                        or char == ':' \
                        or char == '\'':
                    main_temp1 = main_temp1[:-1]
                    main_temp2 = main_temp2[:-1]
                main_temp1 += BIGNUMMATRIX[char][0]
                main_temp2 += BIGNUMMATRIX[char][1]
            except Exception:
                traceback.print_exc()
                pass

        if LCD_ROWS == 2:
            if self._current_program % 2 == 0 and io_status.message == '':
                # +----------------+
                # |_ XXX XXX XXX°  |
                # |M XXX XXX.XXX   |
                # +----------------+
                self.set_charset(CHARSET_BIGNUM)

                if config.MODULE_TEMP and self._current_program % 4 == 0:
                    self.line[0] = '{} {}'.format(heating_icon,
                                                  main_temp1.center(14))
                    self.line[1] = '{} {}'.format(mode_icon,
                                                  main_temp2.center(14))
                else:
                    self.line[0] = main_temp1.center(LCD_COLUMNS + 1)[0:LCD_COLUMNS]
                    self.line[1] = main_temp2.center(LCD_COLUMNS + 1)[0:LCD_COLUMNS]
            else:
                # +----------------+
                # |_ 11:41   22.3°C|
                # |A  20.6° > 19:30|
                # +----------------+
                # self.set_charset(CHARSET_SYMBOL) # change charset
                self.line[0] = '{} {:02.0f}^{:02.0f}   {}'.format(
                    heating_icon,
                    datetime.datetime.now().hour,
                    datetime.datetime.now().minute,
                    '{:.1f}\xDFC'.format(io_status.int_temp_c) if config.MODULE_TEMP else '' )
                if io_status.message != '':
                    self.line[1] = ' \xA5 \xA5 \xA5 ' + \
                                   io_status.message + ' \xA5 \xA5 \xA5'
                else:
                    self.line[1] = line2options
        else:
            # +--------------------+
            # | _ 12:09 19-01-2018 |
            # |    -=0 0-0 0-0°    |
            # |    0__ 0_0.0_0     |
            # |A  17.0°C > 18:00   |
            # +--------------------+
            self.line[0] = '{} {:02.0f}^{:02.0f} {}'.format(
                heating_icon,
                datetime.datetime.now().hour, datetime.datetime.now().minute,
                datetime.datetime.today().strftime('%d-%m-%Y')).center(LCD_COLUMNS)
            self.line[1] = main_temp1.center(LCD_COLUMNS + 1)[0:LCD_COLUMNS]
            self.line[2] = main_temp2.center(LCD_COLUMNS + 1)[0:LCD_COLUMNS]
            if io_status.message != '':
                self.line[3] = ' \xA5 \xA5 \xA5 ' + \
                               io_status.message + ' \xA5 \xA5 \xA5'
            else:
                self.line[3] = line2options
            self.line[3] = self.line[3].center(LCD_COLUMNS)

        # if program is changed, reset positions
        if change:
            self.position = [-LCD_LINE_DELAY] * LCD_ROWS

    def update(self, io_status, refresh_requested=False, draw=True):
        global CURRENT_CHARSET, NEW_CHARSET
        if DISPLAY_TYPE == NONE or PAUSED:
            return 0

        start_time = datetime.datetime.now()
        tmp_lines = [''] * LCD_ROWS

        # backlight change timeout expired: set backlight with no timeout
        if datetime.datetime.now() > self._backlight_change:
            self.set_backlight(not self._is_backlit)

        if draw and (self._is_backlit or refresh_requested):
            if CURRENT_CHARSET != NEW_CHARSET:
                CURRENT_CHARSET = NEW_CHARSET
                self.cleanup()
                self._load_charset()

        blink_off = datetime.datetime.now().second % 2 != 0

        # lines update
        if datetime.datetime.now() >= self._message_timeout:
            self._command = ''

        for no in range(0, LCD_ROWS):
            if self._command:
                if no == int(LCD_ROWS / 2):
                    tmp_lines[no] = self._command.center(LCD_COLUMNS)
                else:
                    tmp_lines[no] = ' ' * LCD_COLUMNS
            else:
                if len(self.line[no]) > LCD_COLUMNS:
                    self.position[no] += 1
                    if self.position[no] > len(
                            self.line[no]) - LCD_COLUMNS + LCD_LINE_DELAY:
                        self.position[no] = -LCD_LINE_DELAY
                position = 0 if self.position[no] < 0 else \
                    len(self.line[no]) - LCD_COLUMNS if self.position[no] > \
                    len(self.line[no]) - LCD_COLUMNS else \
                    self.position[no]
                cur_line = self.line[no][position:len(self.line[no])].ljust(
                    LCD_COLUMNS)[0:LCD_COLUMNS]
                tmp_lines[no] = cur_line

            if blink_off:
                tmp_lines[no] = tmp_lines[no].replace('\xA5', ' ')
                tmp_lines[no] = tmp_lines[no].replace('^', ' ')
                tmp_lines[no] = tmp_lines[no].replace('@', ' ')
                tmp_lines[no] = tmp_lines[no].replace('¶', ' ')
            else:
                tmp_lines[no] = tmp_lines[no].replace('^', ':')
                tmp_lines[no] = tmp_lines[no].replace('@', '<')
                tmp_lines[no] = tmp_lines[no].replace('¶', '>')

            # show switch command on lowest right
            switch_on = False
            for sw in range(len(config.BUTTONS)):
                switch_on |= io_status.sw_status[sw]
            if switch_on and no == LCD_ROWS - 1:
                tmp_lines[no] = tmp_lines[no][:-2] + ' #'

            if draw and (self._is_backlit or refresh_requested):
                if self.old_line[no] != tmp_lines[no]:
                    self.old_line[no] = tmp_lines[no]
                    self.lcd.lcd_display_string(tmp_lines[no], no)

        self.echo_display(tmp_lines)
        return (datetime.datetime.now() - start_time).total_seconds()

    def cleanup(self):
        if DISPLAY_TYPE == NONE or PAUSED:
            return

        if DISPLAY_TYPE == I2C_LCD:
            self.lcd.lcd_clear()
        else:
            # on RPiGPIO lcd_clear breaks..
            for row in range(0, LCD_ROWS):
                self.lcd.lcd_display_string(' ' * LCD_COLUMNS, row)
        self.echo_display([' ' * LCD_COLUMNS] * LCD_ROWS)

    def set_backlight(self, state, timeout=datetime.datetime(9999, 12, 31)):
        global CURRENT_CHARSET, NEW_CHARSET

        if DISPLAY_TYPE == NONE or PAUSED:
            return

        # set backlight and re-initialize LCD screen text on backlight on
        if state and not self._is_backlit:
            if CURRENT_CHARSET != NEW_CHARSET:
                CURRENT_CHARSET = NEW_CHARSET
                self.cleanup()
                self._load_charset()

            for row in range(0, LCD_ROWS):
                self.lcd.lcd_display_string(self.line[row], row)
        self.lcd.set_backlight(state)

        self._is_backlit = state
        self._backlight_change = timeout

    def show_command(self, message):
        self._command = '@@ ' + message + ' ¶¶'
        self._message_timeout = datetime.datetime.now() + datetime.timedelta(seconds=3)

    def echo_display(self, lines):
        # move cursor home
        sys.stdout.write("\x1b[H")
        if CURRENT_CHARSET == CHARSET_SYMBOL:
            replace_chars = ['*', '+', '=', 'A', 'M', '?', '?', '?', '>', '°',
                             '?', '.']
        else:
            replace_chars = ['*', '+', '=', 'A', 'M', '-', '_', '=', '>', '°',
                             '0', '.']

        print(' ' * (LCD_COLUMNS + 4))
        print(' +' +
              ('-' * LCD_COLUMNS) + '+ ' if self._is_backlit else
              ' +' + '- ' * int(LCD_COLUMNS / 2) + '+ ')
        for row in range(0, LCD_ROWS):
            count = 0
            cur_row = lines[row]
            for char in '\x00\x01\x02\x03\x04\x05\x06\x07\x7E\xDF\xFF\xA5':
                cur_row = cur_row.replace(char, replace_chars[count])
                count += 1
            print(' |{}| '.format(cur_row))
        print(' +' + ('-' * LCD_COLUMNS) + '+ ' if self._is_backlit
              else ' +' + '- ' * int(
            LCD_COLUMNS / 2) + '+ ')
        print(' ' * int(LCD_COLUMNS + 4))
        # restore cursor pos
        sys.stdout.write("\x1b8")
