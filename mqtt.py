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

import traceback
import config
import re
import time
import datetime

from utils import LOG_INFO, log_stdout, log_stderr, LOG_DEBUG, LOG_WARN
from paho.mqtt import client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion

CONNECT_TIMEOUT_SECS = 5

class MQTT:
    def __init__(self, io_status):
        self.__running = self.__connected = False
        self.__areas = {}
        self.__io_status = io_status
        self.__client = None

    def __connect_mqtt(self) -> mqtt_client:
        def on_connect(client, userdata, flags, rc, properties):
            if flags.session_present:
                pass
            if rc == 0:
                log_stdout('MQTT', 'Connected to broker {}:{}'
                           .format(config.MQTT_BROKER, config.MQTT_PORT), LOG_INFO)
                self.__connected = True
            else:
                log_stderr('*MQTT* - Failed to connect to broker {}:{}: {}'.
                           format(config.MQTT_BROKER, config.MQTT_PORT, rc))

        def on_disconnect(client, userdata, flags, rc, properties):
            if rc == 0:
                # successful disconnect
                log_stdout('MQTT', 'Disconnected: ok', LOG_INFO)
                self.__connected = False
            else:
                # error processing
                log_stderr('*MQTT* - Failed to disconnect: {}'.format(rc))

        self.__connected = False
        _client = mqtt_client.Client(CallbackAPIVersion.VERSION2)
        # client.username_pw_set(username, password)
        _client.on_connect = on_connect
        _client.on_disconnect = on_disconnect
        _client.connect(config.MQTT_BROKER, config.MQTT_PORT)
        _client.loop_start()

        start_time = datetime.datetime.now()
        while not self.__connected and \
            (datetime.datetime.now() - start_time).total_seconds() < CONNECT_TIMEOUT_SECS:
            time.sleep(.1)

        if config.LOG_LEVEL == LOG_DEBUG:
            _client.subscribe("$SYS/broker/log/#")
        return _client

    def __publish(self, area_id, req_temp_c, calibration):
        area = self.__areas[area_id]
        if area['mqtt_trv_name']:
            topic = '{}/{}/set'.format(config.MQTT_BASE_TOPIC, area['mqtt_trv_name'])
            payload = (area['mqtt_trv_publish_payload']
                      .replace('**TEMP**', str(req_temp_c))
                      .replace('**TEMP_CAL**', str(calibration)))
            if self.__client:
                self.__client.publish(topic, payload)
                log_stdout('MQTT', 'Area: {} - Publish: req. temp.: {}, calibration: {}'.
                           format(area['area_name'], req_temp_c, calibration, LOG_INFO))
            else:
                log_stdout('MQTT', 'Missing client - Publish SKIPPED {} -> ({})'.
                           format(payload, topic, LOG_WARN))

    def update_areas(self):
        for area_id in self.__io_status.areas.keys():
            area = self.__io_status.areas[area_id]
            if not area['published']:
                # lazy MQTT server connection
                if not self.__connected:
                    try:
                        self.__client = self.__connect_mqtt()
                    except Exception as e:
                        log_stderr('*MQTT* - Failed to connect: {}'.format(e))
                        break
                self.__publish(area_id, area['req_temp_c'], area['temp_calibration'])
                area['published'] = True

    def subscribe(self, area_id, area_name,
                  mqtt_name, cur_temp_c_regex, req_temp_c_regex, calibration,
                  mqtt_trv_name, mqtt_trv_publish_payload, subscribed):
        def on_message(client, userdata, msg):
            msg_topic = "DEBUG" if msg.topic.startswith("$SYS/broker/log/") else msg.topic
            log_stdout('MQTT', '({}) -> {}'.format(msg_topic, msg.payload.decode()), LOG_DEBUG)
            for area_id in self.__areas.keys():
                area = self.__areas[area_id]
                if area['topic'] == msg.topic:
                    cur_area = self.__io_status.areas[area_id]
                    cur_area["last_update"] = datetime.datetime.now().isoformat()
                    cur_area['temp_calibration'] = area['calibration']
                    temp = re.search(area['cur_temp_c_regex'], msg.payload.decode())
                    cur_temp_c = float(temp.group(1)) if temp else 999
                    if area['req_temp_c_regex']:
                        temp = re.search(area['req_temp_c_regex'], msg.payload.decode())
                        req_temp_c = float(temp.group(1)) if temp else 0
                        cur_area['req_temp_c'] = req_temp_c
                    else:
                        req_temp_c = "-"
                    cur_area['cur_temp_c'] = cur_temp_c
                    log_stdout('MQTT', '{} update - cur_temp_c: {} - req_temp_c: {}'.
                               format(area['mqtt_name'], cur_temp_c, req_temp_c), LOG_INFO)

        topic = '{}/{}'.format(config.MQTT_BASE_TOPIC, mqtt_name)
        self.__areas[area_id] = \
            { 'area_name': area_name,
              'topic': topic, 'mqtt_name': mqtt_name,
              'cur_temp_c_regex': cur_temp_c_regex, 'req_temp_c_regex': req_temp_c_regex,
              'calibration': calibration, 'mqtt_trv_name': mqtt_trv_name,
              'mqtt_trv_publish_payload': mqtt_trv_publish_payload }
        if self.__client and not subscribed:
            self.__client.subscribe(topic)
            self.__client.on_message = on_message
            log_stdout('MQTT', 'Area: {} - subscribe ({})'.format(area_name, topic), LOG_INFO)


    def cleanup(self):
        log_stdout('MQTT', 'Cleanup', LOG_INFO)
        if self.__client:
            self.__client.loop_stop()
            self.__client.disconnect()
        self.__running = False
        self.__areas.clear()
