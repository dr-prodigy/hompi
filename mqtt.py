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

import config
import json

from datetime import datetime
from utils import LOG_INFO, log_stdout, log_stderr

next_publish = datetime.now()

def update_trv(io_status, io_system):
    global next_publish, old_entity

    for trv in io_status.trv_status: # type: ignore
        current_trv = io_status.trv_status[trv]
        if not current_trv["published"]:
            log_stdout("MQTT", "{}: req_temp_c = {}, calibration = {}".
                        format(trv, current_trv["req_temp_c"], current_trv["calibration"]),
                        LOG_INFO)
            try:
                # TODO: do update
                current_trv["published"] = True
            except Exception as e:
                log_stderr('*MQTT* ERR: UPDATE_TRV ({}): {}'.format(trv, e))
