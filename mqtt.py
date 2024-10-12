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
import re

from utils import LOG_INFO, log_stdout, log_stderr, LOG_DEBUG
from paho.mqtt import client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion

class MQTT:
    def __init__(self):
        self.__client = None
        self.__running = False

    @staticmethod
    def __connect_mqtt() -> mqtt_client:
        def on_connect(client, userdata, flags, rc, properties):
            if flags.session_present:
                pass
            if rc == 0:
                log_stdout("MQTT", "Connected to MQTT broker {}:{}"
                           .format(config.MQTT_BROKER, config.MQTT_PORT), LOG_INFO)
            else:
                log_stderr("Failed to connect, return code {}\n".format(rc))

        def on_disconnect(client, userdata, flags, rc, properties):
            if rc == 0:
                # success disconnect
                log_stdout("MQTT", "Disconnect OK", LOG_INFO)
            else:
                # error processing
                log_stderr("Failed to disconnect, return code {}\n".format(rc))

        client = mqtt_client.Client(CallbackAPIVersion.VERSION2)
        # client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.connect(config.MQTT_BROKER, config.MQTT_PORT)
        return client

    def update_trv(self, io_status):
        for trv in io_status.areas:  # type: ignore
            current_trv = io_status.areas[trv]
            if not current_trv["published"]:
                log_stdout("MQTT", "{}: req_temp_c = {}, temp_calibration = {}".
                           format(trv, current_trv["req_temp_c"], current_trv["temp_calibration"]),
                           LOG_INFO)
                try:
                    # TODO: do update
                    current_trv["published"] = True
                except Exception as e:
                    log_stderr('MQTT ERR: UPDATE_TRV ({}): {}'.format(trv, e))

    def run(self, io_status):
        if not self.__running:
            def on_message(client, userdata, msg):
                log_stdout("MQTT", "Message: {}".format(msg.payload.decode()), LOG_INFO)
                cur_temp = None
                result = re.search('"energy":([0-9.-]*),', msg.payload.decode())
                if result:
                    cur_temp = result.group(1)
                log_stdout("MQTT", "Update from {} - cur_temp: {}".format(msg.topic, cur_temp))

            self.__client = self.__connect_mqtt()
            for area in io_status.areas.values():
                area_name = area["area"]
                topic = "{}/{}".format(config.MQTT_BASE_TOPIC, area["mqtt_temp_name"])
                self.__client.subscribe(topic)
                self.__client.on_message = on_message
                log_stdout("MQTT", "Area {}: subscribed to {}".format(area_name, topic), LOG_INFO)

            self.__client.loop_start()
            self.__running = True

    def cleanup(self):
        self.__client.loop_stop()
