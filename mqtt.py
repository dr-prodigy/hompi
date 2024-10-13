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
        self.__running = False
        self.__client = self.__connect_mqtt()
        self.__areas = {}
        self.__io_status = None

    @staticmethod
    def __connect_mqtt() -> mqtt_client:
        def on_connect(client, userdata, flags, rc, properties):
            if flags.session_present:
                pass
            if rc == 0:
                log_stdout('MQTT', 'Connected to MQTT broker {}:{}'
                           .format(config.MQTT_BROKER, config.MQTT_PORT), LOG_INFO)
            else:
                log_stderr('Failed to connect, return code {}\n'.format(rc))

        def on_disconnect(client, userdata, flags, rc, properties):
            if rc == 0:
                # success disconnect
                log_stdout('MQTT', 'Disconnect OK', LOG_INFO)
            else:
                # error processing
                log_stderr('Failed to disconnect, return code {}\n'.format(rc))

        client = mqtt_client.Client(CallbackAPIVersion.VERSION2)
        # client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.connect(config.MQTT_BROKER, config.MQTT_PORT)
        return client

    def __publish(self, area_id, req_temp_c, calibration):
        def on_publish(client, userdata, result):
            print("data published \n")
            pass

        area = self.__areas[area_id]
        if area['mqtt_trv_name']:
            topic = '{}/{}'.format(config.MQTT_BASE_TOPIC, area['mqtt_trv_name'])
            payload = (area['mqtt_trv_publish_payload']
                      .replace('**TEMP**', str(req_temp_c))
                      .replace('**TEMP_CAL**', str(calibration)))
            self.__client.on_publish = on_publish
            self.__client.publish(topic, payload)
            log_stdout('MQTT', 'Publishing to {}: {}'.
                       format(topic, payload, LOG_INFO))

    def update_areas(self):
        for area_id in self.__io_status.areas.keys():
            area = self.__io_status.areas[area_id]
            if not area['published']:
                self.__publish(area_id, area['req_temp_c'], area['temp_calibration'])
                area['published'] = True

    def subscribe(self, area_id, area_name,
                  mqtt_name, decoding_regex, calibration,
                  mqtt_trv_name, mqtt_trv_publish_payload):
        def on_message(client, userdata, msg):
            log_stdout('MQTT', 'Message: {}'.format(msg.payload.decode()), LOG_INFO)
            for area_id in self.__areas.keys():
                decoder = self.__areas[area_id]
                if decoder['topic'] == msg.topic:
                    mqtt_name = decoder['mqtt_name']
                    regex = decoder['decoding_regex']
                    calibration = decoder['calibration']
                    result = re.search(regex, msg.payload.decode())
                    if result:
                        cur_temp = float(result.group(1)) + calibration
                        log_stdout('MQTT', 'Update from {} - cur_temp: {}'.format(mqtt_name, cur_temp))
                        self.__io_status.areas[area_id]['cur_temp_c'] = cur_temp

        topic = '{}/{}'.format(config.MQTT_BASE_TOPIC, mqtt_name)
        self.__areas[area_id] = \
            { 'topic': topic,
              'mqtt_name': mqtt_name, 'decoding_regex': decoding_regex, 'calibration': calibration,
              'mqtt_trv_name': mqtt_trv_name, 'mqtt_trv_publish_payload': mqtt_trv_publish_payload }
        self.__client.subscribe(topic)
        self.__client.on_message = on_message
        log_stdout('MQTT', 'Area {}: subscribed to {}'.format(area_name, topic), LOG_INFO)

    def run(self, io_status):
        if not self.__running:
            self.__running = True
            self.__io_status = io_status
            self.__client.loop_start()
            log_stdout('MQTT', 'Loop started', LOG_INFO)

    def cleanup(self):
        log_stdout('MQTT', 'cleanup', LOG_INFO)
        self.__client.loop_stop()
        self.__areas.clear()
