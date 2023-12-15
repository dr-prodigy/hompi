#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
# Copyright (C)2018-23 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
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
import traceback
import urllib3
from utils import log_stderr
from requests import post

if not config.HASS_CHECK_SSL_CERT:
    urllib3.disable_warnings()

STATUS_ENTITY_API_URL = "api/states/sensor."

def publish_status(io_status):
    json_str = io_status.get_output()
    json_obj = json.loads(json_str)

    status_entities = [
        {"entity_id": "hompi_id",
         "data": {"state": json_obj["id"], "attributes":
            {"friendly_name": "Hompi id", "icon": "mdi:home"}}},
        {"entity_id": "hompi_mode",
         "data": {"state": json_obj["mode_desc"], "attributes":
            {"friendly_name": "Hompi mode", "icon": "mdi:table"}}},
        {"entity_id": "hompi_target",
         "data": {
             "state": "{} ({} °C) until h. {:0>5.2f}".format(
             json_obj["req_temp_desc"], json_obj["req_temp_c"], int(json_obj["req_end_time"]) / 100),
             "attributes":
            {"friendly_name": "Hompi target", "icon": "mdi:target"}}},
        {"entity_id": "hompi_heating_status",
         "data": {
             "state": json_obj["heating_status"],
             "attributes":
                 {"friendly_name": "Hompi heating status", "icon": "mdi:heat-wave"}}},
    ]
    if config.MODULE_TEMP:
        status_entities.append(
        {"entity_id": "hompi_temperature",
         "data": {"state": "{:.1f}".format(json_obj["int_temp_c"]), "attributes":
            {"friendly_name": "Hompi temperature", "icon": "mdi:thermometer",
             "device_class": "temperature", "unit_of_measurement": "°C"}}}
        )
    if config.MODULE_APHORISM:
        status_entities.append(
        {"entity_id": "forismatic",
         "data": {"state": "{} ({})".format(json_obj["aphorism_text"].strip(), json_obj["aphorism_author"].strip()),
                  "attributes": {"friendly_name": "Forismatic", "icon": "mdi:card-text"}}}
        )
    if config.MODULE_AMBIENT:
        status_entities.extend([
        {"entity_id": "hompi_ambient_color",
         "data": {"state": json_obj["current_ambient_color"], "attributes":
             {"friendly_name": "Hompi ambient color", "icon": "mdi:palette"}}},
        {"entity_id": "hompi_ambient_command",
         "data": {"state": json_obj["current_ambient_command"], "attributes":
             {"friendly_name": "Hompi ambient command", "icon": "mdi:palette"}}}
        ])

    for entity in status_entities:
        try:
            entity_id = entity["entity_id"]
            url = config.HASS_SERVER + STATUS_ENTITY_API_URL + entity_id
            headers = {"Authorization": "Bearer " + config.HASS_TOKEN, "content-type": "application/json"}

            response = post(url, headers=headers, json=entity["data"], verify=config.HASS_CHECK_SSL_CERT)
            if config.VERBOSE_LOG:
                print('HASS PUBLISH ({}): {}'.format(entity_id, response.text))
        except Exception:
            log_stderr('HASS PUBLISH ({}): {}'.format(entity_id, traceback.format_exc()))
