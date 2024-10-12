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

from utils import LOG_INFO, log_stdout, log_stderr
from paho.mqtt import client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion

class MQTT:
    def __init__(self):
        self.__client = self.__connect_mqtt()

    @staticmethod
    def __connect_mqtt() -> mqtt_client:
        def on_connect(client, userdata, flags, rc, properties):
            if flags.session_present:
                pass
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code {}\n".format(rc))

        def on_disconnect(client, userdata, flags, rc, properties):
            if rc == 0:
                # success disconnect
                print("Disconnect OK")
            else:
                # error processing
                print("Failed to disconnect, return code {}\n".format(rc))

        client = mqtt_client.Client(CallbackAPIVersion.VERSION2)
        # client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.connect(config.MQTT_BROKER, config.MQTT_PORT)
        return client

    @staticmethod
    def subscribe(client: mqtt_client):
        def on_message(client, userdata, msg):
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

        client.subscribe("{}/{}".format(config.MQTT_BASE_TOPIC, "Smartplug1"))
        client.on_message = on_message

    @staticmethod
    def update_trv(io_status):
        for trv in io_status.trv_status:  # type: ignore
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

    def run(self):
        self.subscribe(self.__client)
        self.__client.loop_start()

    def cleanup(self):
        self.__client.loop_stop()
