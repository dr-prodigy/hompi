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
AMBIENT_MAX_BRIGHTNESS = 0xFF

AMBIENT_ENABLED = False
try:
    AMBIENT_ENABLED = config.MODULE_AMBIENT
except Exception:
    pass

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


def _do_ambient_color(color, brightness):
    color = _apply_brightness(color, brightness)
    command = AMBIENT_MODULE_CMD + \
              AMBIENT_SET_COLOR_COMMAND.format(color) + ' &'
    print('*AMBIENT* do color - Executing: {}'.format(command))
    if AMBIENT_ENABLED:
        os.system(command)


def _do_ambient_crossfade(previous_color, previous_brightness, color, brightness):
    previous_color = _apply_brightness(previous_color, previous_brightness)
    color = _apply_brightness(color, brightness)

    command = AMBIENT_MODULE_CMD + \
              AMBIENT_CROSSFADE_COMMAND.format(
                  color, previous_color) + ' &'
    print('*AMBIENT* crossfade - Executing: {}'.format(command))
    if AMBIENT_ENABLED:
        os.system(command)


def _do_go_to_sleep(color):
    command = AMBIENT_MODULE_CMD + \
              AMBIENT_GOING_TO_SLEEP_COMMAND.format(color) + ' &'
    print('*AMBIENT* go_to_sleep - Executing: {}'.format(command))
    if AMBIENT_ENABLED:
        os.system(command)


def _apply_brightness(color, brightness):
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
        self.status_on_off = self._status_previous_on_off = False
        self.status_color = self._status_previous_color = 0
        self.status_color_dec = [0, 0, 0]
        self.status_brightness = self._status_previous_brightness = 0
        self.status_effect = self._status_previous_effect = None
        self._status_effect_params = None
        self._status_effect_repeated = False
        self._status_screen_ctrl_code = -1
        self._power_off_time = datetime.datetime(9999, 12, 31)
        self._set_color(AMBIENT_COLOR_OFF)
        # effect list
        self.effect_list = ['xmas_daisy', 'tv_sim', 'stop_effect', 'reset']
        self.effect_list_repeated = [True, True, False, False]

        try:
            self.reset()
        except KeyboardInterrupt:
            raise
        except Exception:
            log_stderr(traceback.format_exc())
            log_stderr('*AMBIENT* ERR : init failed - disabling AMBIENT')
            AMBIENT_ENABLED = False

    def _set_color(self, rgb_string):
        self._status_previous_color = self.status_color
        color = rgb_string
        if rgb_string[0] == '(' and rgb_string[-1] == ')':
            rgb = rgb_string[1:-1].split(',')
            color = "{:0>2}{:0>2}{:0>2}".format(
                hex(int(rgb[0]))[2:], hex(int(rgb[1]))[2:], hex(int(rgb[2]))[2:])
        self.status_color = color

        # decode decimal color
        current_r = int(self.status_color, 16) >> 16 & AMBIENT_MAX_BRIGHTNESS
        current_g = int(self.status_color, 16) >> 8 & AMBIENT_MAX_BRIGHTNESS
        current_b = int(self.status_color, 16) & AMBIENT_MAX_BRIGHTNESS
        self.status_color_dec = [current_r, current_g, current_b]

        # find saturation to apply (avoid division by 0)
        saturation = 255.0 / max(current_r, current_g, current_b, 1)

        # locate nearest color for screen output
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
            self._status_screen_ctrl_code if self.status_on_off else CTRL_CODE_OFF,
            "*" * LED_STRIP_ELEMENTS))

        # restore cursor pos and color
        sys.stdout.write("\033[0m\x1b8")

    def reset(self):
        _do_cleanup()
        # reset and power off
        self.status_on_off = False
        self._set_color(AMBIENT_COLOR_OFF)
        self.status_brightness = 0
        self._power_off_time = datetime.datetime(9999, 12, 31)
        self.status_effect = self._status_effect_params = None
        self._status_effect_repeated = False
        self.reset_changes()

    def set_ambient_on_off(self, status,
                           timeout=datetime.datetime(9999, 12, 31)):
        print("*AMBIENT* on_off {}".format(status))
        self.status_on_off = status
        if status:
            # switch on
            # if color not set, initialize to full light
            if not self.status_color \
                    or self.status_color == AMBIENT_COLOR_OFF:
                self._set_color(AMBIENT_COLOR_ON)
            # if brightness not set, initialize to full light
            if not self.status_brightness:
                self.status_brightness = AMBIENT_MAX_BRIGHTNESS
            # power off time
            self._power_off_time = timeout
        else:
            # reset and power off
            self._power_off_time = datetime.datetime(9999, 12, 31)
            self.status_effect = self._status_effect_params = None
            self._status_effect_repeated = False
        self.update()

    def set_ambient_color(self, color,
                          timeout=datetime.datetime(9999, 12, 31)):
        print("*AMBIENT* color {}".format(color))
        # reset effect
        self.status_effect = self._status_effect_params = None
        self._status_effect_repeated = False
        # power on/off
        self.set_ambient_on_off(color != AMBIENT_COLOR_OFF, timeout)
        # set color
        self._set_color(color)
        self.update()

    def set_ambient_color_hs(self, color,
                              timeout=datetime.datetime(9999, 12, 31)):
        print("*AMBIENT* color_hsv {}".format(color))
        color_hsv = color[1:-1].split(",")
        h = float(color_hsv[0]) / 360
        s = float(color_hsv[1]) / 100
        (r, g, b) = colorsys.hsv_to_rgb(h, 1.0, s)
        self.set_ambient_color("({},{},{})".format(int(r*255), int(g*255), int(b*255)), timeout)

    def set_ambient_brightness(self, brightness):
        print("*AMBIENT* brightness {}".format(brightness))
        # reset effect
        self.status_effect = self._status_effect_params = None
        self._status_effect_repeated = False
        # power on/off
        self.set_ambient_on_off(brightness != 0)
        # set brightness
        self.status_brightness = brightness
        self.update()

    def set_ambient_effect(self, effect, params,
                           timeout=datetime.datetime(9999, 12, 31)):
        effect = effect.lower()
        if effect in self.effect_list:
            print('*AMBIENT* effect {} {}'.format(effect, params))
            # power on
            self.set_ambient_on_off(True, timeout)
            # set effect
            self.status_effect = effect
            self._status_effect_params = params
            # set effect repetition
            self._status_effect_repeated = \
                self.effect_list_repeated[self.effect_list.index(effect)]
        else:
            log_stderr("*AMBIENT* ERR: effect {} not available".format(effect))
        self.update()

    def ambient_ack(self):
        command = AMBIENT_MODULE_CMD + \
                  AMBIENT_ACK_COMMAND.format(
                      'ff0000', self.status_color) + ' &'
        print('*AMBIENT* ack - Executing: {}'.format(command))
        if AMBIENT_ENABLED:
            os.system(command)

    def update(self):
        if datetime.datetime.now() > self._power_off_time:
            # power off timeout expired: go to sleep
            _do_go_to_sleep(self.status_color)
            # power off
            self.set_ambient_on_off(False)
            self.reset_changes()
        elif self.status_effect and self._status_previous_effect != self.status_effect:
            if self.status_effect == 'reset':
                self.reset()
            elif self.status_effect == 'stop_effect':
                # force light to previous state
                self._status_previous_on_off = False
            else:
                # run effect
                _do_effect(self.status_effect, self._status_effect_params)
                self.reset_changes()
            if not self._status_effect_repeated:
                # stop after first run
                self.status_effect = self._status_effect_params = None
        if self._status_previous_on_off != self.status_on_off:
            # power on / off
            old_color = self._status_previous_color if not self.status_on_off else AMBIENT_COLOR_OFF
            old_brightness = self._status_previous_brightness if not self.status_on_off else 0
            new_color = self.status_color if self.status_on_off else AMBIENT_COLOR_OFF
            new_brightness = self.status_brightness if self.status_on_off else 0
            _do_ambient_crossfade(old_color, old_brightness, new_color, new_brightness)
        elif self._status_previous_color != self.status_color \
                or self._status_previous_brightness != self.status_brightness:
            # color change
            _do_ambient_crossfade(self._status_previous_color, self._status_previous_brightness,
                                       self.status_color, self.status_brightness)
        self.reset_changes()

        # update screen
        self._echo_display()

    def reset_changes(self):
        self._status_previous_on_off = self.status_on_off
        self._status_previous_effect = self.status_effect
        self._status_previous_color = self.status_color
        self._status_previous_brightness = self.status_brightness

    def ambient_redo(self):
        if not self.status_on_off:
            print('*AMBIENT* redo CLEANUP')
            _do_cleanup()
        elif self.status_effect and self._status_effect_repeated:
            print('*AMBIENT* redo effect {}'.format(self.status_effect))
            _do_effect(self.status_effect, self._status_effect_params)
        elif self.status_color and self.status_on_off:
            print('*AMBIENT* redo color {}'.format(self.status_color))
            _do_ambient_color(self.status_color, self.status_brightness)


def _do_effect(effect, params):
    command = AMBIENT_MODULE_CMD + \
              '{} {} &'.format(effect, params)
    print('*AMBIENT* effect {} - Executing: {}'.format(effect, command))
    if AMBIENT_ENABLED:
        os.system(command)
