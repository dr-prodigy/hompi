#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from math import isnan

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
import urllib3
import dateutil.parser

from requests import post
from utils import log_stdout, log_stderr
from datetime import datetime, timedelta
from utils import LOG_DEBUG, LOG_INFO, LOG_WARN, LOG_ERROR

if not config.HASS_CHECK_SSL_CERT:
    urllib3.disable_warnings()

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
HOMPI_TEMP_ALERT_ICON = "mdi:thermometer-alert"
HOMPI_UPDATE_ICON = "mdi:update"
HOMPI_APHORISM_ICON = "mdi:comment-quote"
HOMPI_AMBIENT_ICON = "mdi:television-ambient-light"
HOMPI_AMBIENT_EFFECT_ICON = "mdi:palette"

RETRY_MINUTES = 2
REFRESH_MINUTES = 10

headers = {"Authorization": "Bearer " + config.HASS_TOKEN, "content-type": "application/json"}
old_entity = {}
refresh_time = publish_time = datetime.now()

def publish_status(io_status, io_system, ambient):
    global refresh_time, publish_time, old_entity
    hass_entities = []
    now = datetime.now()

    # refresh time: cleanup old status
    if datetime.now() >= refresh_time:
        refresh_time = now + timedelta(minutes=REFRESH_MINUTES)
        old_entity = {}

    if old_entity.get("hompi_id") != io_status.id:
        old_entity["hompi_id"] = io_status.id
        hass_entities.append(
            {"entity_id": "hompi_id",
             "data": {"state": io_status.id, "attributes": {"friendly_name": "Id", "icon": HOMPI_ID_ICON}}}
        )
    if old_entity.get("hompi_mode") != io_status.mode_desc:
        old_entity["hompi_mode"] = io_status.mode_desc
        hass_entities.append(
            {"entity_id": "hompi_mode",
             "data": {"state": io_status.mode_desc, "attributes": {"friendly_name": "Mode", "icon": HOMPI_MODE_ICON}}}
        )

    target = ""
    if io_status.req_temp_desc != "Off":
        req_temp_desc = io_status.req_temp_desc
        req_temp_c = io_status.req_temp_c
        if config.MODULE_TRV:
            if io_status.req_area_temps:
                req_temp_desc = 'Zones'
                req_temp_c = io_status.req_area_temps
            if io_status.get_area_manual_set():
                req_temp_desc += '+M'
        target = "{} ({} °C) until h. {:0>5.2f}".format(req_temp_desc, req_temp_c,
                                                        io_status.req_end_time / 100)
    else:
        target = io_status.req_temp_desc

    if old_entity.get("hompi_target") != target:
        old_entity["hompi_target"] = target
        hass_entities.append(
            {"entity_id": "hompi_target",
             "data": {
                 "state": target,
                 "attributes":
                     {"friendly_name": "Target", "icon": HOMPI_TARGET_ICON}}}
        )

    if old_entity.get("hompi_heating_status") != io_status.heating_status:
        old_entity["hompi_heating_status"] = io_status.heating_status
        hass_entities.append(
            {"entity_id": "hompi_heating_status",
             "data": {
                 "state": io_status.heating_status,
                 "attributes": {"friendly_name": "Heating", "icon":
                     HOMPI_HEATING_WARMING_ICON if io_status.heating_status == "warming" else
                     HOMPI_HEATING_ON_ICON if io_status.heating_status == "on" else
                     HOMPI_HEATING_COOLING_ICON if io_status.heating_status == "cooling" else
                     HOMPI_HEATING_OFF_ICON }}}
        )

    # thermometer entities
    if config.MODULE_TEMP and old_entity.get("hompi_temperature") != io_status.int_temp_c:
        old_entity["hompi_temperature"] = io_status.int_temp_c
        hass_entities.append(
            {"entity_id": "hompi_temperature",
             "data": {"state": "{:.1f}".format(io_status.int_temp_c), "attributes":
                 {"friendly_name": "Hompi temperature", "icon": HOMPI_TEMP_ICON,
                  "device_class": "temperature", "unit_of_measurement": "°C"}}}
        )
    # aphorism entities
    if config.MODULE_APHORISM:
        state = "{} ({})".format(io_status.aphorism_text.strip(), io_status.aphorism_author.strip())
        if old_entity.get("forismatic") != state:
            old_entity["forismatic"] = state
            hass_entities.append(
                {"entity_id": "forismatic",
                "data": {"state": state,
                        "attributes": {"friendly_name": "Forismatic", "icon": HOMPI_APHORISM_ICON}}}
            )
    # ambient light entities
    if config.MODULE_AMBIENT: 
        comparer = "{}{}{}{}{}{}".format(io_status.ambient_on, io_status.id,
                                ambient.status_brightness, ambient.status_color_dec, ambient.status_color_hs,
                                ambient.status_effect)
        if old_entity.get("hompi_ambient_light") != comparer:
            old_entity["hompi_ambient_light"] = comparer
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

    # area entities
    if config.MODULE_TRV:
        for area in io_status.areas.values():
            area_name = "hompi_area_{}".format(area["area"]).lower()
            update_change = False
            icon = HOMPI_TEMP_ICON # default icon
            if "last_update" in area:
                entity_name = "{}_updated".format(area_name)
                last_update = dateutil.parser.parse(area["last_update"])
                updated = (now - last_update).total_seconds() < config.TRV_DATA_EXPIRATION_SECS \
                            and last_update > dateutil.parser.parse(io_status.last_change)
                if old_entity.get(entity_name) != updated:
                    old_entity[entity_name] = updated
                    icon = HOMPI_TEMP_ALERT_ICON if not updated else HOMPI_TEMP_ICON
                    update_change = True

            for ent in ["req_temp_c", "cur_temp_c"]:
                entity_name = "{}_{}".format(area_name, ent)
                if area[ent] != 0 and area[ent] != 999 and (old_entity.get(entity_name) != area[ent] or update_change):
                        old_entity[entity_name] = area[ent]
                        hass_entities.append(
                            {"entity_id": entity_name,
                             "data": {"state": area[ent], "attributes":
                                 {"friendly_name": "Target" if ent == "req_temp_c" else "Temp", "icon": icon,
                                  "device_class": "temperature", "unit_of_measurement": "°C", "id": entity_name}}}
                        )

    # temperature entities
    for temp in io_system.temperatures:
        description = str(temp["description"])
        if old_entity.get("hompi_temp_{}".format(description.lower())) != temp["id"]:
            old_entity["hompi_temp_{}".format(description.lower())] = temp["id"]
            hass_entities.append(
                {"entity_id": "hompi_temp_{}".format(description.lower()),
                 "data": {"state": temp["temp_c"], "attributes":
                     {"friendly_name": "Hompi temp {}".format(description.upper()), "icon": HOMPI_TEMP_ICON,
                      "device_class": "temperature", "unit_of_measurement": "°C", "id": temp["id"]}}}
            )

    entity_id = None
    try:
        if len(hass_entities) > 0 and now >= publish_time:
            log_stdout('HASS', 'Publishing {} entities to HASS'.format(len(hass_entities)), LOG_INFO)
            for entity in hass_entities:
                entity_id = entity["entity_id"]
                url = config.HASS_SERVER + STATUS_ENTITY_API_URL + entity_id
                response = post(url, headers=headers, json=entity["data"], verify=config.HASS_CHECK_SSL_CERT)
                log_stdout('HASS', 'PUBLISH ({}): {}'.format(entity_id, response.text), LOG_INFO)
    except Exception as e:
        # error: cleanup old_entity and delay next publish for RETRY_MINUTES
        log_stderr('*HASS* ERR: PUBLISH ({}): {} -> delaying {} mins'.format(entity_id, e, RETRY_MINUTES))
        publish_time = refresh_time = now + timedelta(minutes=RETRY_MINUTES)
