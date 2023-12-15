#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C)2018-23 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
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

import os
import sys
import datetime
import traceback

import config

from utils import log_stderr

LEDSTRIP_ELEMENTS = 32

AMBIENT_ENABLED = False
try:
    AMBIENT_ENABLED = config.MODULE_AMBIENT
except Exception:
    pass

AMBIENT_MODULE_CMD = 'python ws2801_program.py '

color_RGB_to_ASCII_Ctrl = [
    ('30', 0x000000, 'black'),  # black
    ('31', 0xff0000, 'red'),  # red
    ('32', 0x00ff00, 'green'),  # green
    ('33', 0xffff00, 'yellow'),  # yellow
    ('34', 0x0000ff, 'blue'),  # blue
    ('35', 0xff00ff, 'purple'),  # purple
    ('36', 0x00ffff, 'cyan'),  # cyan
    ('37', 0xffffff, 'white'),  # white
]


class Ambient():
    def __init__(self):
        global AMBIENT_ENABLED

        self._poweroff_time = datetime.datetime(9999, 12, 31)
        self._current_ambient_command = ''
        self._set_current_ambient_color('000000')

        try:
            if AMBIENT_ENABLED:
                self.cleanup()
        except KeyboardInterrupt:
            raise
        except Exception:
            log_stderr(traceback.format_exc())
            log_stderr(
                '*AMBIENT ERR* : LED strip init failed - disabling AMBIENT')
            AMBIENT_ENABLED = False

    def _set_current_ambient_color(self, RGB_string):
        self._current_ambient_color = RGB_string
        self._find_ambient_display_color_no()

    def _find_ambient_display_color_no(self):
        # decode color
        current_r = int(self._current_ambient_color, 16) >> 16 & 0xFF
        current_g = int(self._current_ambient_color, 16) >> 8 & 0xFF
        current_b = int(self._current_ambient_color, 16) & 0xFF

        # find saturation to apply (avoid division by 0)
        saturate_coeff = 255.0 / max(current_r, current_g, current_b, 1)

        # locate nearest color
        min_color_diff = 0xff + 0xff + 0xff
        self._current_ambient_display_color_no = -1
        for color_no in range(0, len(color_RGB_to_ASCII_Ctrl)):
            r = color_RGB_to_ASCII_Ctrl[color_no][1] >> 16 & 0xFF
            g = color_RGB_to_ASCII_Ctrl[color_no][1] >> 8 & 0xFF
            b = color_RGB_to_ASCII_Ctrl[color_no][1] & 0xFF
            new_color_diff =\
                abs(r - current_r * saturate_coeff) + \
                abs(g - current_g * saturate_coeff) + \
                abs(b - current_b * saturate_coeff)
            if new_color_diff < min_color_diff:
                min_color_diff = new_color_diff
                self._current_ambient_display_color_no = color_no

    def _echo_display(self):
        # move cursor home
        # set color and print ledstrip
        sys.stdout.write("\x1b7\x1b[H\033[1;{};40m {} ".format(
            color_RGB_to_ASCII_Ctrl[self._current_ambient_display_color_no][0],
            "*" * LEDSTRIP_ELEMENTS))

        # restore cursor pos and color
        sys.stdout.write("\033[0m\x1b8")

    def _set_ambient_color_command(self, color):
        command = AMBIENT_MODULE_CMD
        command += config.AMBIENT_SETCOLOR_COMMAND.format(color) + ' &'
        return command

    def cleanup(self):
        if not AMBIENT_ENABLED or not config.AMBIENT_INIT_COMMAND:
            return

        # reset poweroff
        self._poweroff_time = datetime.datetime(9999, 12, 31)

        command = AMBIENT_MODULE_CMD
        command += config.AMBIENT_INIT_COMMAND + ' &'
        print('*AMBIENT cleanup* - Executing: {}'.format(command))
        os.system(command)
        self._set_current_ambient_color('000000')
        self._current_ambient_command = ''

    def update(self):
        if not AMBIENT_ENABLED:
            return

        try:
            # poweroff timeout expired: going to sleep
            if datetime.datetime.now() > self._poweroff_time:
                self.going_to_sleep()
            self._echo_display()
            return self._current_ambient_color
        except KeyboardInterrupt:
            raise
        except Exception:
            pass

    def going_to_sleep(self):
        if not AMBIENT_ENABLED:
            return

        # reset poweroff
        self._poweroff_time = datetime.datetime(9999, 12, 31)

        command = AMBIENT_MODULE_CMD
        if config.AMBIENT_GOING_TO_SLEEP_COMMAND:
            command += config.AMBIENT_GOING_TO_SLEEP_COMMAND.format(
                self._current_ambient_color) + ' &'
        else:
            # going to sleep missing: default to INIT
            command += config.AMBIENT_INIT_COMMAND + ' &'
        print('*AMBIENT going_to_sleep* - Executing: {}'.format(command))
        os.system(command)
        self._set_current_ambient_color('000000')

        # refresh command
        self._current_ambient_command = \
            self._set_ambient_color_command('000000')

    def set_ambient_color(self, color,
                              timeout=datetime.datetime(9999, 12, 31)):
        if not AMBIENT_ENABLED or not config.AMBIENT_SETCOLOR_COMMAND:
            return

        command = self._set_ambient_color_command(color)
        print('*AMBIENT setcolor* - Executing: {}'.format(command))
        os.system(command)

        self._poweroff_time = timeout

        # no refresh command (only ambient color)
        self._set_current_ambient_color(color)
        self._current_ambient_command = ''

        return color

    def set_ambient_crossfade(self, color,
                              timeout=datetime.datetime(9999, 12, 31)):
        if not AMBIENT_ENABLED or not config.AMBIENT_CROSSFADE_COMMAND:
            return

        if self._current_ambient_color != color or color == '000000':
            command = AMBIENT_MODULE_CMD
            command += config.AMBIENT_CROSSFADE_COMMAND.format(
                color,
                self._current_ambient_color) + ' &'
            print('*AMBIENT crossfade* - Executing: {}'.format(command))
            os.system(command)

            self._poweroff_time = timeout

            # no refresh command (only ambient color)
            self._set_current_ambient_color(color)
            self._current_ambient_command = ''
        return color

    def set_ambient_xmas_daisy(self, brightness = 1, rgb = ''):
        if not AMBIENT_ENABLED or not config.AMBIENT_XMAS_DAISY_COMMAND:
            return
        command = AMBIENT_MODULE_CMD
        command += config.AMBIENT_XMAS_DAISY_COMMAND.format(
            brightness, rgb) + ' &'
        print('*AMBIENT xmas_daisy* - Executing: {}'.format(command))
        os.system(command)

        # refresh command (repeat)
        self._set_current_ambient_color('000000')
        self._current_ambient_command = command

    def set_ambient_tv_sim(self):
        if not AMBIENT_ENABLED or not config.AMBIENT_TV_SIM_COMMAND:
            return
        command = AMBIENT_MODULE_CMD
        command += config.AMBIENT_TV_SIM_COMMAND + ' &'
        print('*AMBIENT tv_sim* - Executing: {}'.format(command))
        os.system(command)

        # refresh command (repeat)
        self._set_current_ambient_color('000000')
        self._current_ambient_command = command

    def ambient_ack(self):
        if not AMBIENT_ENABLED or not config.AMBIENT_ACK_COMMAND:
            return

        command = AMBIENT_MODULE_CMD
        command += config.AMBIENT_ACK_COMMAND.format(
            'ff0000',
            self._current_ambient_color) + ' &'
        print('*AMBIENT ack* - Executing: {}'.format(command))
        os.system(command)

    def ambient_refresh(self):
        if not AMBIENT_ENABLED:
            return

        if self._current_ambient_command:
            print('*AMBIENT refresh* - Executing: {}'.format(
                self._current_ambient_command))
            os.system(self._current_ambient_command)
        else:
            print('*AMBIENT refresh* - Resetting color to {}'
                  .format(self._current_ambient_color))
            self.set_ambient_color(self._current_ambient_color)

        return self._current_ambient_color
