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
import colorsys

import config

from utils import log_stderr

LED_STRIP_ELEMENTS = 32

AMBIENT_MODULE_CMD = 'python ws2801_program.py '
AMBIENT_CLEAR_COMMAND = 'clear'
AMBIENT_SET_COLOR_COMMAND = 'set_color {}'
AMBIENT_CROSSFADE_COMMAND = 'crossfade {} {}'
AMBIENT_GOING_TO_SLEEP_COMMAND = 'going_to_sleep {}'
AMBIENT_ACK_COMMAND = 'curtain_in_out {} {}'

AMBIENT_COLOR_OFF = '000000'
AMBIENT_COLOR_ON = 'FFFFFF'
AMBIENT_COLOR_OFF_HS = [0, 0]
AMBIENT_COLOR_ON_HS = [0, 0]
AMBIENT_MIN_BRIGHTNESS = 0x00
AMBIENT_MAX_BRIGHTNESS = 0xFF

# effect list
EFFECT_LIST = ['xmas_daisy', 'tv_sim', 'test_loop', 'rainbow', 'rainbow_cycle', 'theater_chase_rainbow',
               'stop_effect', 'reset']
EFFECT_LIST_REPEATED = [True, True, True, True, True, True, False, False]

AMBIENT_ENABLED = False
try:
    AMBIENT_ENABLED = config.MODULE_AMBIENT
except Exception:
    pass

# RGB to control codes
rgb2ctrl_code = [
    ('30', 0x000000, 'black'),  # black
    ('31', 0xff0000, 'red'),  # red
    ('32', 0x00ff00, 'green'),  # green
    ('33', 0xffff00, 'yellow'),  # yellow
    ('34', 0x0000ff, 'blue'),  # blue
    ('35', 0xff00ff, 'purple'),  # purple
    ('36', 0x00ffff, 'cyan'),  # cyan
    ('37', 0xffffff, 'white'),  # white
]
CTRL_CODE_OFF = rgb2ctrl_code[0][0]


def _do_cleanup():
    command = AMBIENT_MODULE_CMD + AMBIENT_CLEAR_COMMAND + ' &'
    print('*AMBIENT* cleanup - Executing: {}'.format(command))
    if AMBIENT_ENABLED:
        os.system(command)

def _do_effect(effect, params):
    command = AMBIENT_MODULE_CMD + \
              '{} {} &'.format(effect, params)
    print('*AMBIENT* effect {} - Executing: {}'.format(effect, command))
    if AMBIENT_ENABLED:
        os.system(command)

def _do_ambient_color(color, brightness):
    color = _rgb_brightness2rgb(color, brightness)
    command = AMBIENT_MODULE_CMD + \
              AMBIENT_SET_COLOR_COMMAND.format(0, color) + ' &'
    print('*AMBIENT* do color - Executing: {}'.format(command))
    if AMBIENT_ENABLED:
        os.system(command)

def _do_ambient_crossfade(color_start, brightness_start, color_end, brightness_end):
    color_start = _rgb_brightness2rgb(color_start, brightness_start)
    color_end = _rgb_brightness2rgb(color_end, brightness_end)

    command = AMBIENT_MODULE_CMD + \
              AMBIENT_CROSSFADE_COMMAND.format(0, color_start, color_end) + ' &'
    print('*AMBIENT* crossfade - Executing: {}'.format(command))
    if AMBIENT_ENABLED:
        os.system(command)

def _do_go_to_sleep(color):
    command = AMBIENT_MODULE_CMD + \
              AMBIENT_GOING_TO_SLEEP_COMMAND.format(0, color) + ' &'
    print('*AMBIENT* go_to_sleep - Executing: {}'.format(command))
    if AMBIENT_ENABLED:
        os.system(command)

def _rgb_brightness2rgb(color, brightness):
    r = float(int(color, 16) >> 16 & AMBIENT_MAX_BRIGHTNESS)
    g = float(int(color, 16) >> 8 & AMBIENT_MAX_BRIGHTNESS)
    b = float(int(color, 16) & AMBIENT_MAX_BRIGHTNESS)
    cur_brightness = float(max(r, g, b, 1))
    brightness = float(brightness)

    return "{:0>2}{:0>2}{:0>2}".format(
        hex(int(r / cur_brightness * brightness))[2:],
        hex(int(g / cur_brightness * brightness))[2:],
        hex(int(b / cur_brightness * brightness))[2:])

class Ambient:
    def __init__(self):
        global AMBIENT_ENABLED

        self.EFFECT_LIST = EFFECT_LIST
        self._newstatus_power_on = self.status_power_on = False
        self._newstatus_color = self.status_color = AMBIENT_COLOR_OFF
        self._newstatus_color_hs = self.status_color_hs = AMBIENT_COLOR_OFF_HS
        self._newstatus_brightness = self.status_brightness = AMBIENT_MIN_BRIGHTNESS
        self._newstatus_effect = self.status_effect = self._newstatus_effect_params = self.status_effect_params = None
        self._newstatus_power_off_time = self.status_power_off_time = datetime.datetime(9999, 12, 31)
        self.status_color_dec = [0, 0, 0]
        self._status_screen_ctrl_code = -1
        self._set_newstatus_color(AMBIENT_COLOR_OFF)

        try:
            self.reset()
        except KeyboardInterrupt:
            raise
        except Exception:
            log_stderr(traceback.format_exc())
            log_stderr('*AMBIENT* ERR : init failed - disabling AMBIENT')
            AMBIENT_ENABLED = False

    def reset(self):
        _do_cleanup()
        # reset and power off
        self._newstatus_power_on = False
        self._set_newstatus_color(AMBIENT_COLOR_OFF)
        self._newstatus_color_hs = AMBIENT_COLOR_OFF_HS
        self._newstatus_brightness = 0
        self._newstatus_effect = self._newstatus_effect_params = None
        self._newstatus_power_off_time = datetime.datetime(9999, 12, 31)
        self.program_change_completed()

    def _set_newstatus_color(self, rgb_string):
        color = rgb_string
        if rgb_string[0] == '(' and rgb_string[-1] == ')':
            rgb = rgb_string[1:-1].split(',')
            color = "{:0>2}{:0>2}{:0>2}".format(
                hex(int(rgb[0]))[2:], hex(int(rgb[1]))[2:], hex(int(rgb[2]))[2:])
        self._newstatus_color = color

    def _update_color_values(self):
        # update RGB decimal color
        current_r = int(self._newstatus_color, 16) >> 16 & AMBIENT_MAX_BRIGHTNESS
        current_g = int(self._newstatus_color, 16) >> 8 & AMBIENT_MAX_BRIGHTNESS
        current_b = int(self._newstatus_color, 16) & AMBIENT_MAX_BRIGHTNESS
        self.status_color_dec = [current_r, current_g, current_b]

        # set nearest color for echo display (debug)
        saturation = 255.0 / max(current_r, current_g, current_b, 1)
        min_color_diff = 0xff + 0xff + 0xff
        for color_no in range(0, len(rgb2ctrl_code)):
            r = rgb2ctrl_code[color_no][1] >> 16 & AMBIENT_MAX_BRIGHTNESS
            g = rgb2ctrl_code[color_no][1] >> 8 & AMBIENT_MAX_BRIGHTNESS
            b = rgb2ctrl_code[color_no][1] & AMBIENT_MAX_BRIGHTNESS
            new_color_diff = \
                abs(r - current_r * saturation) + \
                abs(g - current_g * saturation) + \
                abs(b - current_b * saturation)
            if new_color_diff < min_color_diff:
                min_color_diff = new_color_diff
                self._status_screen_ctrl_code = rgb2ctrl_code[color_no][0]

    def _echo_display(self):
        # move cursor home
        # set color and print led strip
        sys.stdout.write("\x1b7\x1b[H\033[1;{};40m {} ".format(
            self._status_screen_ctrl_code if self._newstatus_power_on else CTRL_CODE_OFF,
            "*" * LED_STRIP_ELEMENTS))

        # restore cursor pos and color
        sys.stdout.write("\033[0m\x1b8")

    def set_ambient_on_off(self, status, timeout=datetime.datetime(9999, 12, 31), do_update=True):
        print("*AMBIENT* on_off {}".format(status))
        if status:
            # switch on
            # if no color is set, switch on to full light
            if not self.status_color \
                    or self.status_color == AMBIENT_COLOR_OFF \
                    or (self.status_color_hs == AMBIENT_COLOR_OFF_HS \
                and self.status_brightness == AMBIENT_MIN_BRIGHTNESS):
                self._set_newstatus_color(AMBIENT_COLOR_ON)
                self._newstatus_color_hs = AMBIENT_COLOR_ON_HS
            # if brightness is 0, initialize to full light
            if not self._newstatus_brightness:
                self._newstatus_brightness = AMBIENT_MAX_BRIGHTNESS
            # power off time
            self._newstatus_power_off_time = timeout
        else:
            # reset effect and power off time
            self._newstatus_power_off_time = datetime.datetime(9999, 12, 31)
            self._newstatus_effect = self.newstatus_effect_params = None

        self._newstatus_power_on = status
        if do_update:
            self.update()

    def set_ambient_color(self, color, timeout=datetime.datetime(9999, 12, 31), do_update=True):
        print("*AMBIENT* set_ambient_color {}".format(color))
        # reset effect
        self._newstatus_effect = self._newstatus_effect_params = None
        # power on/off
        self.set_ambient_on_off(color != AMBIENT_COLOR_OFF, timeout, False)
        # set color
        self._set_newstatus_color(color)
        if do_update:
            self.update()

    def set_ambient_color_hs(self, color, timeout=datetime.datetime(9999, 12, 31), do_update=True):
        print("*AMBIENT* set_ambient_color_hs {}".format(color))
        color_hs = color[1:-1].split(",")
        h = float(color_hs[0])
        s = float(color_hs[1])
        self._newstatus_color_hs = [h, s]
        (r, g, b) = colorsys.hsv_to_rgb(h / 360, 1.0, s / 100)
        self.set_ambient_color("({},{},{})".format(int(r*255), int(g*255), int(b*255)), timeout, do_update)

    def set_ambient_brightness(self, brightness, do_update=True):
        print("*AMBIENT* brightness {}".format(brightness))
        # reset effect
        self._newstatus_effect = self._newstatus_effect_params = None
        # power on/off
        self.set_ambient_on_off(brightness != 0, do_update = False)
        # set brightness
        self._newstatus_brightness = brightness
        if do_update:
            self.update()

    def set_ambient_effect(self, effect, params, timeout=datetime.datetime(9999, 12, 31), do_update=True):
        effect = effect.lower()
        if effect in EFFECT_LIST:
            print('*AMBIENT* effect {} {}'.format(effect, params))
            # power on
            self.set_ambient_on_off(True, timeout, False)
            # set effect
            self._newstatus_effect = effect
            self._newstatus_effect_params = params
        else:
            log_stderr("*AMBIENT* ERR: effect {} not available".format(effect))
        if do_update:
            self.update()

    def ambient_ack(self):
        command = AMBIENT_MODULE_CMD + \
                  AMBIENT_ACK_COMMAND.format(
                      1, 'ff0000', self._newstatus_color, 0, False) + ' &'
        print('*AMBIENT* ack - Executing: {}'.format(command))
        if AMBIENT_ENABLED:
            os.system(command)

    def update(self):
        if datetime.datetime.now() > self.status_power_off_time:
            # GO TO SLEEP
            _do_go_to_sleep(self.status_color)
            # power off
            self.set_ambient_on_off(False)
            self.program_change_completed()
        elif self.status_effect != self._newstatus_effect:
            # EFFECTS
            if self._newstatus_effect == 'reset':
                # reset light and internal status
                self.reset()
                # self.program_change_completed()  # IMPLICIT
            elif self._newstatus_effect == 'stop_effect':
                # stop effect
                self._newstatus_effect = self._newstatus_effect_params = None
                # force program change (=> return to previous state)
                self.status_power_on = not self._newstatus_power_on
                # PROGRAM CHANGE NOT COMPLETED!
            elif self._newstatus_effect:
                # run effect
                _do_effect(self._newstatus_effect, self._newstatus_effect_params)
                # auto-reset effect
                if not EFFECT_LIST_REPEATED[EFFECT_LIST.index(self._newstatus_effect)]:
                    self._newstatus_effect = self._newstatus_effect_params = None
                self.program_change_completed()

        # LIGHT & COLORS
        if self.status_power_on != self._newstatus_power_on:
            color_start = self.status_color
            brightness_start = self.status_brightness
            color_end = self._newstatus_color
            brightness_end = self._newstatus_brightness
            if self._newstatus_power_on:
                # power off
                color_start = AMBIENT_COLOR_OFF
                brightness_start = AMBIENT_MIN_BRIGHTNESS
            else:
                # power on
                color_end = AMBIENT_COLOR_OFF
                brightness_end = AMBIENT_MIN_BRIGHTNESS
            _do_ambient_crossfade(color_start, brightness_start, color_end, brightness_end)
        elif self.status_color != self._newstatus_color \
             or self.status_brightness != self._newstatus_brightness:
            # color change
            _do_ambient_crossfade(self.status_color, self.status_brightness,
                                  self._newstatus_color, self._newstatus_brightness)

        self.program_change_completed()

        # update screen
        self._echo_display()

    def program_change_completed(self):
        self.status_power_on = self._newstatus_power_on
        self.status_effect = self._newstatus_effect
        self.status_effect_params = self._newstatus_effect_params
        self.status_color = self._newstatus_color
        self.status_color_hs = self._newstatus_color_hs
        self.status_brightness = self._newstatus_brightness
        self.status_power_off_time = self._newstatus_power_off_time
        self._update_color_values()

    def ambient_redo(self):
        if not self.status_power_on:
            print('*AMBIENT* redo CLEANUP')
            _do_cleanup()
        elif self.status_effect:
            print('*AMBIENT* redo effect {}'.format(self.status_effect))
            _do_effect(self.status_effect, self.status_effect_params)
        elif self.status_color and self.status_power_on:
            print('*AMBIENT* redo color {}'.format(self._newstatus_color))
            _do_ambient_color(self._newstatus_color, self._newstatus_brightness)
