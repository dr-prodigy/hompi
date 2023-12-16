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

LED_STRIP_ELEMENTS = 32

AMBIENT_ENABLED = False
try:
    AMBIENT_ENABLED = config.MODULE_AMBIENT
except Exception:
    pass

AMBIENT_MODULE_CMD = 'python ws2801_program.py '

rgb2ascii_ctrl = [
    ('30', 0x000000, 'black'),  # black
    ('31', 0xff0000, 'red'),  # red
    ('32', 0x00ff00, 'green'),  # green
    ('33', 0xffff00, 'yellow'),  # yellow
    ('34', 0x0000ff, 'blue'),  # blue
    ('35', 0xff00ff, 'purple'),  # purple
    ('36', 0x00ffff, 'cyan'),  # cyan
    ('37', 0xffffff, 'white'),  # white
]


class Ambient:
    def __init__(self):
        global AMBIENT_ENABLED
        self.status_on_off = False
        self.status_color = None
        self.status_color_dec = None
        self.status_command = None
        self.status_screen_color_no = -1
        self.power_off_time = datetime.datetime(9999, 12, 31)
        self._update_internal_state('000000')

        try:
            if AMBIENT_ENABLED:
                self.cleanup()
        except KeyboardInterrupt:
            raise
        except Exception:
            log_stderr(traceback.format_exc())
            log_stderr('*AMBIENT ERR* : init failed - disabling AMBIENT')
            AMBIENT_ENABLED = False

    def _do_ambient_color(self, color):
        if self.status_on_off:
            command = AMBIENT_MODULE_CMD
            command += config.AMBIENT_SETCOLOR_COMMAND.format(color) + ' &'
            print('*AMBIENT do color* - Executing: {}'.format(command))
            os.system(command)

    def _update_internal_state(self, rgb_string):
        color = rgb_string
        if rgb_string[0] == '(' and rgb_string[-1] == ')':
            rgb = rgb_string[1:-1].split(',')
            color = hex(rgb[0])[2:] + hex(rgb[1])[2:] + hex(rgb[2])[2:]
        self.status_color = color

        # decode decimal color
        current_r = int(self.status_color, 16) >> 16 & 0xFF
        current_g = int(self.status_color, 16) >> 8 & 0xFF
        current_b = int(self.status_color, 16) & 0xFF
        self.status_color_dec = [current_r, current_g, current_b]

        # find saturation to apply (avoid division by 0)
        saturation = 255.0 / max(current_r, current_g, current_b, 1)

        # locate nearest color for screen output
        min_color_diff = 0xff + 0xff + 0xff
        for color_no in range(0, len(rgb2ascii_ctrl)):
            r = rgb2ascii_ctrl[color_no][1] >> 16 & 0xff
            g = rgb2ascii_ctrl[color_no][1] >> 8 & 0xff
            b = rgb2ascii_ctrl[color_no][1] & 0xff
            new_color_diff = \
                abs(r - current_r * saturation) + \
                abs(g - current_g * saturation) + \
                abs(b - current_b * saturation)
            if new_color_diff < min_color_diff:
                min_color_diff = new_color_diff
                self.status_screen_color_no = color_no

    def _do_go_to_sleep(self):
        if AMBIENT_ENABLED:
            # reset power off
            self.power_off_time = datetime.datetime(9999, 12, 31)

            command = AMBIENT_MODULE_CMD
            if config.AMBIENT_GOING_TO_SLEEP_COMMAND:
                command += config.AMBIENT_GOING_TO_SLEEP_COMMAND.format(
                    self.status_color) + ' &'
            else:
                # going to sleep missing: default to INIT
                command += config.AMBIENT_INIT_COMMAND + ' &'
            print('*AMBIENT going_to_sleep* - Executing: {}'.format(command))
            os.system(command)

            # switch off
            self._do_ambient_color('000000')
            self.status_on_off = False

    def _echo_display(self):
        # move cursor home
        # set color and print led strip
        sys.stdout.write("\x1b7\x1b[H\033[1;{};40m {} ".format(
            rgb2ascii_ctrl[self.status_screen_color_no][0],
            "*" * LED_STRIP_ELEMENTS))

        # restore cursor pos and color
        sys.stdout.write("\033[0m\x1b8")

    def cleanup(self):
        if AMBIENT_ENABLED and config.AMBIENT_INIT_COMMAND:
            # reset power off time
            self.power_off_time = datetime.datetime(9999, 12, 31)

            command = AMBIENT_MODULE_CMD
            command += config.AMBIENT_INIT_COMMAND + ' &'
            print('*AMBIENT cleanup* - Executing: {}'.format(command))
            os.system(command)
            self._update_internal_state('000000')
            self.status_on_off = False
            self.status_command = None

    def update(self):
        try:
            if AMBIENT_ENABLED:
                # power off timeout expired: going to sleep
                if datetime.datetime.now() > self.power_off_time:
                    self._do_go_to_sleep()
                self._echo_display()
        except KeyboardInterrupt:
            raise
        except Exception:
            pass

    def set_ambient_on_off(self, status,
                           timeout=datetime.datetime(9999, 12, 31)):
        if AMBIENT_ENABLED and config.AMBIENT_SETCOLOR_COMMAND:
            if status.upper() == "ON":
                # switch on
                if self.status_color == '000000':
                    # if color not set, initialize to white
                    self._update_internal_state('FFFFFF')
                self.status_on_off = True
                self._do_ambient_color(self.status_color)

                # power off time
                self.power_off_time = timeout
            else:
                # switch off
                self.status_on_off = False
                self._do_ambient_color('000000')

    def set_ambient_color(self, color,
                           timeout=datetime.datetime(9999, 12, 31)):
        if AMBIENT_ENABLED and config.AMBIENT_SETCOLOR_COMMAND:
            self._do_ambient_color(color)

            # power off time
            self.power_off_time = timeout

            # no refresh command (only ambient color)
            self._update_internal_state(color)
            self.status_command = None

    def set_ambient_crossfade(self, color,
                              timeout=datetime.datetime(9999, 12, 31)):
        if AMBIENT_ENABLED and config.AMBIENT_CROSSFADE_COMMAND:
            if self.status_color != color or color == '000000':
                command = AMBIENT_MODULE_CMD
                command += config.AMBIENT_CROSSFADE_COMMAND.format(
                    color,
                    self.status_color) + ' &'
                print('*AMBIENT crossfade* - Executing: {}'.format(command))
                os.system(command)

                # power off time
                self.power_off_time = timeout

                # no refresh command (only ambient color)
                self._update_internal_state(color)
                self.status_command = None

    def set_ambient_effect(self, effect, brightness=1, rgb=''):
        if AMBIENT_ENABLED:
            command = '{} {} {} {} &'.format(AMBIENT_MODULE_CMD, effect, brightness, rgb)
            print('*AMBIENT {}* - Executing: {}'.format(effect, command))
            os.system(command)

            # refresh command (repeat)
            self._update_internal_state('000000')
            self.status_on_off = True
            self.status_command = command

    def ambient_ack(self):
        if AMBIENT_ENABLED and config.AMBIENT_ACK_COMMAND:
            command = AMBIENT_MODULE_CMD
            command += config.AMBIENT_ACK_COMMAND.format(
                'ff0000',
                self.status_color) + ' &'
            print('*AMBIENT ack* - Executing: {}'.format(command))
            os.system(command)

    def ambient_refresh(self):
        if AMBIENT_ENABLED:
            if self.status_command:
                print('*AMBIENT refresh* - Executing: {}'.format(
                    self.status_command))
                os.system(self.status_command)
            else:
                print('*AMBIENT refresh* - Resetting color to {}'
                      .format(self.status_color))
                self._do_ambient_color(self.status_color)

    def get_status(self):
        status = dict(
            color=self.status_color, color_dec=self.status_color_dec,
            on=self.status_on_off, command=self.status_command)
        return status
