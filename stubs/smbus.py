#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2018 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com> <maurizio.montel@gmail.com>
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

import config

DEBUG_LOG = config.VERBOSE_LOG


class SMBus:
    def __init__(self, port):
        if DEBUG_LOG:
            print('__SMBus__ {}'.format(port))

    def write_byte(self, a, b):
        if DEBUG_LOG:
            print('SMBus.write_byte {},{}'.format(a, b))

    def write_cmd_arg(self, a, b):
        if DEBUG_LOG:
            print('SMBus.write_cmd_arg {},{}'.format(a, b))

    def write_block_data(self, a, b):
        if DEBUG_LOG:
            print('SMBus.write_block_data {},{}'.format(a, b))

    def read_byte(self):
        if DEBUG_LOG:
            print('SMBus.read_byte FOO (0xFF)')
        return 0xFF

    def read_byte_data(self, a):
        if DEBUG_LOG:
            print('SMBus.read_byte_data {} (0xFF ...)'.format(a))
        return [0xFF, 0xFF, 0xFF, 0xFF]

    def read_block_data(self, a):
        if DEBUG_LOG:
            print('SMBus.read_block_data {} (0xFF ...)'.format(a))
        return [0xFF, 0xFF, 0xFF, 0xFF]
