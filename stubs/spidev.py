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

# **** Copy / symlink me to project root directory to enable stubbing ****

import config

DEBUG_LOG = config.VERBOSE_LOG


class SpiDev:
    @staticmethod
    def open(port, device):
        if DEBUG_LOG:
            print('SpiDev.open ({},{})'.format(port, device))

    @staticmethod
    def writebytes(data):
        if DEBUG_LOG:
            print('SpiDev.writebytes ({})'.format(data))
