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

import os
import sys
import datetime


def log_stderr(data):
    cur_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sys.stderr.write('{} - {}\n'.format(cur_date, data))


def os_async_command(command):
    os.popen(command)