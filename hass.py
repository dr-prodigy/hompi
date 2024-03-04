#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
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
import traceback
import urllib3

from requests import post
from utils import log_stderr
from datetime import datetime, timedelta

if not config.HASS_CHECK_SSL_CERT:
    urllib3.disable_warnings()

next_publish = datetime.now()

STATUS_ENTITY_API_URL = "api/states/sensor."
HOMPI_ID_ICON = "mdi:home"
HOMPI_MODE_ICON = "mdi:table"
HOMPI_TARGET_ICON = "mdi:target"
# HOMPI_HEATING_OFF_ICON = "mdi:power-off"
# HOMPI_HEATING_OFF_ICON = "mdi:minus"
HOMPI_HEATING_OFF_ICON = "mdi:color-helper"
HOMPI_HEATING_WARMING_ICON = "mdi:radiator-disabled"
HOMPI_HEATING_ON_ICON = "mdi:fire"
HOMPI_HEATING_COOLING_ICON = "mdi:radiator"
HOMPI_TEMP_ICON = "mdi:thermometer"
HOMPI_APHORISM_ICON = "mdi:comment-quote"
HOMPI_AMBIENT_ICON = "mdi:television-ambient-light"
HOMPI_AMBIENT_EFFECT_ICON = "mdi:palette"


def publish_status(io_status, io_system, ambient):
    global next_publish
    hass_entities = [
        {"entity_id": "hompi_id",
         "data": {"state": io_status.id, "attributes": {"friendly_name": "Id", "icon": HOMPI_ID_ICON}}},
        {"entity_id": "hompi_mode",
         "data": {"state": io_status.mode_desc, "attributes": {"friendly_name": "Mode", "icon": HOMPI_MODE_ICON}}},
        {"entity_id": "hompi_target",
         "data": {
             "state": "{} ({} °C) until h. {:0>5.2f}".format
             (io_status.req_temp_desc, io_status.req_temp_c, io_status.req_end_time / 100),
             "attributes":
                 {"friendly_name": "Target", "icon": HOMPI_TARGET_ICON}}},
        {"entity_id": "hompi_heating_status",
         "data": {
             "state": io_status.heating_status,
             "attributes": {"friendly_name": "Heating", "icon":
                 HOMPI_HEATING_WARMING_ICON if io_status.heating_status == "warming" else
                 HOMPI_HEATING_ON_ICON if io_status.heating_status == "on" else
                 HOMPI_HEATING_COOLING_ICON if io_status.heating_status == "cooling" else
                 HOMPI_HEATING_OFF_ICON }}},
    ]
    # thermometer entities
    if config.MODULE_TEMP:
        hass_entities.append(
            {"entity_id": "hompi_temperature",
             "data": {"state": "{:.1f}".format(io_status.int_temp_c), "attributes":
                 {"friendly_name": "Hompi temperature", "icon": HOMPI_TEMP_ICON,
                  "device_class": "temperature", "unit_of_measurement": "°C"}}}
        )
    # aphorism entities
    if config.MODULE_APHORISM:
        hass_entities.append(
            {"entity_id": "forismatic",
             "data": {"state": "{} ({})".format(io_status.aphorism_text.strip(), io_status.aphorism_author.strip()),
                      "attributes": {"friendly_name": "Forismatic", "icon": HOMPI_APHORISM_ICON}}}
        )
    # ambient light entities
    if config.MODULE_AMBIENT:
        light_sensor = {"entity_id": "hompi_ambient_light",
                        "data": {"state": io_status.ambient_on, "attributes":
                            {"unique_id": "hompi_ambient_{}".format(io_status.id.lower()),
                             "friendly_name": "Hompi ambient light",
                             "icon": HOMPI_AMBIENT_ICON,
                             "effect_list": ambient.EFFECT_LIST,
                             }}}
        if ambient.status_power_on:
            light_sensor["data"]["attributes"].update(
                {"brightness": ambient.status_brightness,
                 "rgb_color": ambient.status_color_dec,
                 "hs_color": ambient.status_color_hs})
            if ambient.status_effect:
                light_sensor["data"]["attributes"].update(
                    {"effect": ambient.status_effect, "icon": HOMPI_AMBIENT_EFFECT_ICON})
        hass_entities.append(light_sensor)

    # temperature entities
    for temp in io_system.temperatures:
        description = str(temp["description"])
        hass_entities.append(
            {"entity_id": "hompi_temp_{}".format(description.lower()),
             "data": {"state": temp["temp_c"], "attributes":
                 {"friendly_name": "Hompi temp {}".format(description.upper()), "icon": HOMPI_TEMP_ICON,
                  "device_class": "temperature", "unit_of_measurement": "°C", "id": temp["id"]}}}
        )

    entity_id = None
    try:
        for entity in hass_entities:
            entity_id = entity["entity_id"]
            url = config.HASS_SERVER + STATUS_ENTITY_API_URL + entity_id
            headers = {"Authorization": "Bearer " + config.HASS_TOKEN, "content-type": "application/json"}

            if datetime.now() >= next_publish:
                response = post(url, headers=headers, json=entity["data"], verify=config.HASS_CHECK_SSL_CERT)
                if config.VERBOSE_LOG:
                    print('*HASS* PUBLISH ({}): {}'.format(entity_id, response.text))
    except Exception as e:
        log_stderr('*HASS* ERR: PUBLISH ({}): {}'.format(entity_id, e))
        # exit and delay next publish for 60 secs
        next_publish = datetime.now() + timedelta(seconds=60)
