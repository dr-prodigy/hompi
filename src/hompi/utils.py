#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>
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

import shlex
import subprocess
import sys
import datetime
from .config import config

LOG_GPIO = 0
LOG_DEBUG = 1
LOG_INFO = 2
LOG_WARN = 3
LOG_ERROR = 4

def log_stdout(module, data, log_level=LOG_DEBUG):
    cur_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if log_level >= config.LOG_LEVEL and module not in config.LOG_MUTE_MODULES or \
        log_level > config.LOG_INFO:
        sys.stdout.write("{} - *{}* - {}\n".format(cur_date, module, data))

def log_stderr(data):
    cur_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sys.stderr.write('{} - {}\n'.format(cur_date, data))

def os_async_command(command, timeout=10):
    """Execute a system command safely without shell expansion."""
    try:
        if isinstance(command, (list, tuple)):
            cmd_args = [str(arg) for arg in command]
        else:
            cmd_args = shlex.split(command)
        result = subprocess.run(cmd_args, capture_output=True, text=True, shell=False, timeout=timeout)
        if result.stdout:
            log_stdout('UTILS', result.stdout.strip(), LOG_DEBUG)
        if result.stderr:
            log_stdout('UTILS', result.stderr.strip(), LOG_WARN)
        return result
    except Exception as exc:
        log_stderr('os_async_command error executing {}: {}'.format(command, exc))
        return None
