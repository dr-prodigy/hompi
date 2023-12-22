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

import time
import sys
import os
import math
import signal
import datetime
import random

# GPIO import
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("WARN: RPi.GPIO missing - loading stub library")
    import stubs.RPi.GPIO as GPIO

# Import the WS2801 module.
import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI

# Configure the count of pixels:
PIXEL_COUNT = 32

# Configure transition timings
try:
    import config
    if config and config.AMBIENT_TRANSITION_FRAMES:
        AMBIENT_TRANSITION_FRAMES = float(config.AMBIENT_TRANSITION_FRAMES)
    else:
        AMBIENT_TRANSITION_FRAMES = 100.0
except ImportError:
    print("WARN: config.py missing - loading defaults")
    AMBIENT_TRANSITION_FRAMES = 100.0

AMBIENT_FRAME_DURATION = 1.0 / AMBIENT_TRANSITION_FRAMES

# Alternatively specify a hardware SPI connection on /dev/spidev0.0:
SPI_PORT = 0
SPI_DEVICE = 0

# Kill currently running commands
for line in os.popen("ps ax | grep " + sys.argv[0] +
                     "| grep python | grep -v " + str(os.getpid())):
    fields = line.split()
    pid = fields[0]
    os.kill(int(pid), signal.SIGKILL)


def clear():
    pixels.clear()
    pixels.show()


def set_color(brightness=None, rgb='ffffff', rgb_foo=None, wait=None, reverse=None):
    b = int(rgb, 16) >> 16 & 0xFF
    g = int(rgb, 16) >> 8 & 0xFF
    r = int(rgb, 16) & 0xFF
    for k in range(pixels.count()):
        pixels.set_pixel_rgb(k, r, g, b)
    pixels.show()


def crossfade(brightness=None, rgb_in='000000', rgb_out='ffffff', wait=None, reverse=None):
    rgb = int(rgb_in, 16)
    b_in = rgb >> 16 & 0xFF
    g_in = rgb >> 8 & 0xFF
    r_in = rgb & 0xFF

    rgb = int(rgb_out, 16)
    b_out = rgb >> 16 & 0xFF
    g_out = rgb >> 8 & 0xFF
    r_out = rgb & 0xFF

    for frames in range(int(AMBIENT_TRANSITION_FRAMES + 1)):
        # compute crossfade
        r = int((AMBIENT_TRANSITION_FRAMES - frames)
                / AMBIENT_TRANSITION_FRAMES * r_in +
                frames / AMBIENT_TRANSITION_FRAMES * r_out)
        g = int((AMBIENT_TRANSITION_FRAMES - frames)
                / AMBIENT_TRANSITION_FRAMES * g_in +
                frames / AMBIENT_TRANSITION_FRAMES * g_out)
        b = int((AMBIENT_TRANSITION_FRAMES - frames)
                / AMBIENT_TRANSITION_FRAMES * b_in +
                frames / AMBIENT_TRANSITION_FRAMES * b_out)

        # update color
        for k in range(pixels.count()):
            pixels.set_pixel_rgb(k, r, g, b)
        pixels.show()

        # sleep
        time.sleep(AMBIENT_FRAME_DURATION)


def wipe_in_out(brightness=None, rgb_in='ffffff', rgb_out='000000', wait=.005, reverse=None):
    # re-init to rgb_out
    set_color(rgb_out)
    # run animation
    color_wipe(rgb_in, wait, config.LED_RIGHT_TO_LEFT)
    color_wipe(rgb_out, wait, config.LED_RIGHT_TO_LEFT)


def curtain_in_out(brightness=None, rgb_in='ffffff', rgb_out='000000', wait=.01, reverse=None):
    # re-init to rgb_out
    set_color(rgb_out)
    # run animation
    color_curtain(rgb_in, wait, True)
    color_curtain(rgb_out, wait, True)


# Fill the dots one after the other with a color
def color_wipe(brightness=None, rgb='000000', rgb2=None, wait=.05, reverse=False):
    rgb = int(rgb, 16)
    b = rgb >> 16 & 0xFF
    g = rgb >> 8 & 0xFF
    r = rgb & 0xFF
    i_range = \
        reversed(range(pixels.count())) if reverse else range(pixels.count())
    for i in i_range:
        pixels.set_pixel_rgb(i, r, g, b)
        pixels.show()
        time.sleep(wait)


# Fill the dots one after the other with a color
def color_curtain(brightness=None, rgb='000000', rgb_foo=None, wait=.05, reverse=False):
    rgb = int(rgb, 16)
    b = rgb >> 16 & 0xFF
    g = rgb >> 8 & 0xFF
    r = rgb & 0xFF
    center = int(math.floor(pixels.count() / 2))
    i_range = \
        reversed(range(center)) if reverse else \
        range(center)
    for i in i_range:
        pixels.set_pixel_rgb(center - i - 1, r, g, b)
        pixels.set_pixel_rgb(center + i, r, g, b)
        pixels.show()
        time.sleep(wait)


def go_to_sleep(brightness=None, rgb='ffffff', rgb_foo=None, wait=None, reverse=None):
    rgb = int(rgb, 16)
    b_in = rgb >> 16 & 0xFF
    g_in = rgb >> 8 & 0xFF
    r_in = rgb & 0xFF
    color_in = Adafruit_WS2801.RGB_to_color(r_in, g_in, b_in)
    color_out = Adafruit_WS2801.RGB_to_color(0, 0, 0)

    # blink 10 times
    for counter in (range(20)):
        current_color = color_in if counter % 2 else color_out
        for k in range(pixels.count()):
            pixels.set_pixel(k, current_color)
        pixels.show()
        time.sleep(.5)
    # fade to black ;-)
    crossfade('000000', rgb_in)


def test_loop(brightness=1, rgb1=None, rgb2=None, wait=None, reverse=None):
    # Some example procedures showing how to display to the pixels:
    color_wipe(brightness, rgb1='ff0000', rgb2=None, wait=.05, reverse=None)  # Red
    color_wipe(brightness, rgb1='00ff00', rgb2=None, wait=.05, reverse=None)  # Green
    color_wipe(brightness, rgb1='0000ff', rgb2=None, wait=.05, reverse=None)  # Blue
    # Send a theater pixel chase in...
    theater_chase(brightness, rgb1='7f7f7f', rgb2='', wait=.05, reverse=None)  # White
    theater_chase(brightness, rgb1='7f0000', rgb2='', wait=.05, reverse=None)  # Red
    theater_chase(brightness, rgb1='00007f', rgb2='', wait=.05, reverse=None)  # Blue

    rainbow(brightness, rgb1=None, rgb2=None, wait=.02, reverse=None)
    rainbow_cycle(brightness, rgb1=None, rgb2=None, wait=.02, reverse=None)
    theater_chase_rainbow(brightness, rgb1='00007f', rgb2=None, wait=.05, reverse=None)


def rainbow(brightness=1, rgb_foo1='', rgb_foo2='', wait=.02, reverse=False):
    wait = float(wait)
    for j in range(256):
        for i in range(pixels.count()):
            pixels.set_pixel(i, _color_wheel((i + j) & 255))

        pixels.show()
        time.sleep(wait)


# Slightly different, this makes the rainbow equally distributed throughout
def rainbow_cycle(brightness=1, rgb_foo1='', rgb_foo2='', wait=.02, reverse=False):
    wait = float(wait)
    for j in range(256 * 5):  # 5 cycles of all colors on wheel
        for i in range(pixels.count()):
            pixels.set_pixel(i,
                             _color_wheel(
                                (((int)(i * 256 / pixels.count()) + j)) & 255))

        pixels.show()
        time.sleep(wait)


# Theatre-style crawling lights.
def theater_chase(brightness=1, rgb='ffffff', rgb_foo='', wait=.05, reverse=False):
    wait = float(wait)
    rgb = int(rgb, 16)
    b = rgb >> 16 & 0xFF
    g = rgb >> 8 & 0xFF
    r = rgb & 0xFF
    for j in range(10):  # do 10 cycles of chasing
        for q in range(3):
            for i in range(0, pixels.count(), 3):
                if (i + q < pixels.count()):
                    # turn every 3rd pixel on
                    pixels.set_pixel_rgb(i + q, r, g, b)

            pixels.show()

            time.sleep(wait)

            for i in range(0, pixels.count(), 3):
                if (i + q < pixels.count()):
                    pixels.set_pixel(i + q, 0)  # turn every third pixel off


# Theatre-style crawling lights with rainbow effect
def theater_chase_rainbow(brightness=1, rgb_foo1='', rgb_foo2='', wait=.05, reverse=False):
    wait = float(wait)
    for j in range(256):  # cycle all 256 colors in the wheel
        for q in range(3):
            for i in range(0, pixels.count(), 3):
                if (i + q < pixels.count()):
                    pixels.set_pixel(i + q, _color_wheel(
                        (i + j) % 255))  # turn every third pixel on

            pixels.show()

            time.sleep(wait)

            for i in range(0, pixels.count(), 3):
                if (i + q < pixels.count()):
                    pixels.set_pixel(i+q, 0)  # turn every third pixel off


def xmas_daisy(brightness=1, rgb='', rgb_foo='', wait=.05, reverse=False):
    brightness = float(brightness)
    if rgb:
        rgb = int(rgb, 16)
        b = rgb >> 16 & 0xFF
        g = rgb >> 8 & 0xFF
        r = rgb & 0xFF
        colors = [
            Adafruit_WS2801.RGB_to_color(
                int(r * brightness),
                int(g * brightness),
                int(b * brightness)),
        ]
    else:
        colors = [
            Adafruit_WS2801.RGB_to_color(
                0, 0, int(0xFF * brightness)),  # red
            Adafruit_WS2801.RGB_to_color(
                0, int(0xFF * brightness), 0),  # green
            Adafruit_WS2801.RGB_to_color(
                0, int(0x6B * brightness), int(0xFF * brightness)),  # yellow
            Adafruit_WS2801.RGB_to_color(
                int(0xFF * brightness), 0, 0),  # blue
        ]

    initial_time = datetime.datetime.now()
    while (datetime.datetime.now() - initial_time).total_seconds() < 300:
        switched = random.randint(1, 2)
        flashed = random.randint(1, 2)
        delay = random.uniform(.04, .1)
        for cycles in range(5):
            for frames in range(2):
                for flash in range(1, 21):  # starts with off
                    for i in range(0, pixels.count()):
                        color = colors[i % len(colors)] if (
                                frames % 2 == i % switched and
                                (not flash % flashed))\
                                else 0
                        pixels.set_pixel(i, color)
                    pixels.show()
                    time.sleep(delay)


def tv_sim(brightness='1', rgb_foo1='', rgb_foo2='', wait=.05, reverse=False):
    initial_time = datetime.datetime.now()
    while (datetime.datetime.now() - initial_time).total_seconds() < 300:
        delay = random.uniform(.1, 5)
        r = g = 0xDF
        b = 0xFF
        brightness = random.uniform(.02, 1)
        color = Adafruit_WS2801.RGB_to_color(
            int(r * brightness), int(g * brightness), int(b * brightness))
        for i in range(0, pixels.count()):
            pixels.set_pixel(i, color)
        pixels.show()
        time.sleep(delay)


# Input a value 0 to 255 to get a color value.
# The colours are a transition r - g - b - back to r.
def _color_wheel(wheelPos):
    wheelPos = 255 - wheelPos
    if (wheelPos < 85):
        return Adafruit_WS2801.RGB_to_color(255 - wheelPos * 3, 0,
                                            wheelPos * 3)

    if (wheelPos < 170):
        wheelPos -= 85
        return Adafruit_WS2801.RGB_to_color(0, wheelPos * 3,
                                            255 - wheelPos * 3)

    wheelPos -= 170
    return Adafruit_WS2801.RGB_to_color(wheelPos * 3,
                                        255 - wheelPos * 3, 0)


if __name__ == "__main__":
    switcher = {
        "clear": clear,
        "set_color": set_color,
        "crossfade": crossfade,
        "go_to_sleep": go_to_sleep,
        "test_loop": test_loop,
        "color_wipe": color_wipe,
        "color_curtain": color_curtain,
        "rainbow": rainbow,
        "rainbow_cycle": rainbow_cycle,
        "theater_chase": theater_chase,
        "theater_chase_rainbow": theater_chase_rainbow,
        "wipe_in_out": wipe_in_out,
        "curtain_in_out": curtain_in_out,
        "xmas_daisy": xmas_daisy,
        "tv_sim": tv_sim,
    }

    # Get the function from switcher dictionary
    if len(sys.argv) == 1:
        print("Commands available: {}".format(switcher.keys()))
    else:
        func = switcher.get(sys.argv[1].lower())

        if func:
            # Initialize ledstrip
            pixels = Adafruit_WS2801.WS2801Pixels(
                PIXEL_COUNT, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE), gpio=GPIO)

            # Execute the function
            if len(sys.argv) > 6:
                func(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
            elif len(sys.argv) > 5:
                    func(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
            elif len(sys.argv) > 4:
                func(sys.argv[2], sys.argv[3], sys.argv[4])
            elif len(sys.argv) > 3:
                func(sys.argv[2], sys.argv[3])
            elif len(sys.argv) > 2:
                func(sys.argv[2])
            else:
                func()
        else:
            print("Commands available: {}".format(switcher.keys()))
            print("params: (brightness=0..1, rgb1='xxxxxx', rgb2='xxxxxx', wait=.05, reverse=False)")
