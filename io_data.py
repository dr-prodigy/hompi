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

import json
import datetime

import config

hide_message = None


class Input:
    def __init__(self):
        self.last_update = datetime.datetime.now().isoformat()
        self.data = ''


class Status:
    def __init__(self):
        global hide_message
        # general
        self.id = config.HOMPI_ID
        self.last_update = datetime.datetime.now().isoformat()
        self.last_change = datetime.datetime.now().isoformat()
        self.hompi_slaves = {}
        self.hompi_ext_sensors = {}
        # heating
        if config.MODULE_TEMP:
            self.int_temp_c = 0.0
        self.mode_id = ''
        self.mode_desc = ''
        self.short_mode_desc = ''
        self.timetable_desc = ''
        self.day_type_desc = ''
        self.req_temp_c = 0.0
        self.req_temp_desc = ''
        self.req_start_time = 0
        self.req_end_time = 0
        self.heating_status = 'off'
        # switches
        self.sw_sig = [False]*len(config.BUTTONS)
        self.sw_status = [False]*len(config.BUTTONS)
        # gui
        self.current_image = ''
        self.message = ''
        hide_message = datetime.datetime.now()
        # ambient
        self.current_ambient_color = '000000'
        self.current_ambient_command = ''
        self.ext_temp_c = 0.0
        # meteo
        if config.MODULE_METEO:
            self.place = ''
            self.weather = ''
            self.humidity = 0
            self.pressure = 0
            self.wind = 0.0
        # aphorism
        if config.MODULE_APHORISM:
            self.aphorism_text = ''
            self.aphorism_author = ''

    def get_output(self):
        return json.dumps(self.__dict__, indent=0)

    def get_status_text(self):
        if self.message != '':
            status = '{}'.format(self.message)
        else:
            stato = 'manual' if self.mode_desc == 'Manual' else\
                'automatic' if self.mode_desc == 'Automatic' else\
                'off' if self.mode_desc == 'Off' else 'Winter safe'
            heating = 'off' if self.heating_status == 'off' else\
                'on' if self.heating_status == 'on' else\
                'cooling' if self.heating_status == 'cooling' else\
                'warming'

            status = 'temperature {:.1f} degrees, {} mode'.\
                     format(self.int_temp_c, stato) + \
                     (', {:.1f} degrees required, heating {}'.format(
                        self.req_temp_c, heating)
                         if stato in ['automatic', 'manual'] else
                         '')
        return status

    def update(self, current_time):
        if self.message != '' and hide_message <= current_time:
            self.message = ''
            self.last_change == current_time.isoformat()

    def send_message(self, message):
        global hide_message

        self.message = message.encode('utf-8')
        self.last_change = datetime.datetime.now().isoformat()
        hide_message = datetime.datetime.now() + datetime.timedelta(seconds=40)

    def reset_message(self):
        global hide_message

        self.message = ''
        self.last_change = datetime.datetime.now().isoformat()
        hide_message = datetime.datetime.now()

    def send_switch_command(self, switch):
        self.sw_sig[switch] = True


class SystemInfo:
    def __init__(self):
        self.modules = []
        self.buttons = {}

        if config.MODULE_AMBIENT:
            self.modules.append('ambient')
            self.ambient_commands = ['AMBIENT_XMAS']
        if config.MODULE_APHORISM:
            self.modules.append('aphorism')
        if config.MODULE_DB_LOG:
            self.modules.append('db_log')
        if config.MODULE_LCD:
            self.modules.append('lcd')
        if config.MODULE_METEO:
            self.modules.append('meteo')
        if config.MODULE_TEMP:
            self.modules.append('temp')
        counter = 0
        for sw in config.BUTTONS:
            self.buttons.update({counter: sw[1]})
            counter += 1

    def get_output(self):
        return json.dumps(self.__dict__, indent=0)


def init_test(io_status):
    io_status.ext_temp_c = 6.0
    io_status.req_temp_desc = 'Economy'
    io_status.heating_status = 'off'
    io_status.gate_status = False
