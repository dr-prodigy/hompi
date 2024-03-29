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

import sys
import signal
import time
import datetime
import dateutil.parser
import math
import traceback
import os
import holidays

import config
import db
import hass
import io_data
import sensors
import dashboard
import resources
import ambient
import random

import socket

from tendo import singleton
from utils import os_async_command
from utils import log_stdout, log_stderr, LOG_GPIO, LOG_DEBUG, LOG_INFO, LOG_WARN, LOG_ERROR

io_status = io_data.Status()
io_system = io_data.SystemInfo()
sensor = sensors.Sensors()
lcd = dashboard.Dashboard()
ambient = ambient.Ambient()

TEST_INIT_TEMP = 20.0
TEST_DELTA_EXT_INT_FACTOR = .001
TEST_DELTA_THERMO_ON_TEMP_C = .03
current_status = ''
sig_command = False
is_status_changed = True
is_program_changed = False

initial_time = datetime.datetime.now()
sig_switch_timeout = [datetime.datetime.now()]*len(config.BUTTONS)

temp = temp_avg_accu = temp_avg_sum = 0.0
temp_avg_counter = 0
log_temp_avg_accu = log_temp_avg_sum = 0.0
log_temp_avg_counter = 0

try:
    if config.HOLIDAYS_COUNTRY:
        holiday_list = holidays.country_holidays(config.HOLIDAYS_COUNTRY)
    else:
        log_stdout("HOMPI", "WARN: config.HOLIDAYS_COUNTRY missing, defaulting to IT", LOG_WARN)
        holiday_list = holidays.IT()
except Exception:
    log_stdout("HOMPI", "WARN: config.HOLIDAYS_COUNTRY missing, defaulting to IT", LOG_WARN)
    holiday_list = holidays.IT()

task_every_secs = {
    'hompi_ext_refresh': 61.0,
    'update_lcd_content': 11.0,
    'get_temp': 20.0,
    'get_meteo': 300.0,  # 5 mins
    'get_aphorism': 241.0,  # 4 mins
    'refresh': 120.0,  # 2 min (multiple of get_temp)
    'update_temp': 80.0,
    'update_io': 10.0,
}

task_every_mins = {
    'log': 15.0
}

task_at_secs = {}
task_at_mins = {}

sighup_refresh = True

def main():
    global sig_command, sighup_refresh, is_status_changed, is_program_changed, lcd
    global initial_time
    global temp, temp_avg_accu, temp_avg_counter, temp_avg_sum
    global log_temp_avg_accu, log_temp_avg_counter, log_temp_avg_sum

    last_update_min = -1

    # will sys.exit(-1) if other instance is running
    singleton.SingleInstance()

    # first initializations
    init()

    # main loop
    log_data('start')
    show_message('HOMPI', 'HOMPI START')
    say('Start')

    while True:
        try:
            # save cycle start time
            cycle_start_time = datetime.datetime.now()
            secs_elapsed = round(
                (cycle_start_time - initial_time).total_seconds())
            # time in the day
            current_time = datetime.datetime.today().hour * 100 + \
                datetime.datetime.today().minute

            #  refresh at end time (do once per minute)
            if (io_status.req_end_time == current_time and
                    last_update_min != datetime.datetime.today().minute):
                last_update_min = datetime.datetime.today().minute
                sighup_refresh = True

            # OPERATIONS NOT DONE ON REFRESH - START
            # update external hompis / sensors
            if secs_elapsed >= task_at_secs['hompi_ext_refresh']:
                sensor.hompi_slaves_refresh(io_status.hompi_slaves)
                sensor.hompi_ext_sensors_refresh(io_status.hompi_ext_sensors)

            # update I/O: meteo
            if secs_elapsed >= task_at_secs['get_meteo'] and config.MODULE_METEO:
                meteo()

            # aphorism
            if secs_elapsed >= task_at_secs['get_aphorism'] and config.MODULE_APHORISM:
                aphorism()

            # re-sync things
            if secs_elapsed >= task_at_secs['refresh']:
                # restart LCD
                lcd.refresh_display(io_status)
                # ambient color
                ambient.ambient_redo()
                io_status.set_ambient(ambient)
                # temp sensor failure: reset temp sampling
                if config.MODULE_TEMP and temp_avg_sum == 0:
                    temp_avg_accu = temp_avg_counter = 0.0
                    io_status.int_temp_c = 0.0

            # get temperature
            if (secs_elapsed >= task_at_secs['get_temp']) and config.MODULE_TEMP:
                get_temperature()

            # update temperature
            if (secs_elapsed >= task_at_secs['update_temp']):
                # save new temperature (if valid)
                if temp_avg_sum != 0:
                    io_status.int_temp_c = round(temp_avg_accu / temp_avg_sum, 2)
                # reset temp sampling
                temp_avg_accu = temp_avg_counter = temp_avg_sum = 0
            # OPERATIONS NOT DONE ON REFRESH - END

            # update I/O (ack occurring here gets ambient control)
            if secs_elapsed >= task_at_secs['update_io'] or sighup_refresh:
                process_input()

            # refresh program
            if secs_elapsed >= task_at_secs['refresh'] or sighup_refresh:
                refresh_program(current_time)

            # compute status (heating, switches, ...)
            is_status_changed |= compute_status()

            # update I/O: output
            if secs_elapsed >= task_at_secs['update_io'] or is_status_changed or sighup_refresh:
                update_output()

            # log data (check task_at_mins)
            if (datetime.datetime.now().minute == task_at_mins['log'] or sighup_refresh) and log_temp_avg_sum > 0:
                io_status.int_temp_c = round(
                    log_temp_avg_accu / log_temp_avg_sum, 2)
                log_temp_avg_accu = log_temp_avg_counter = log_temp_avg_sum = 0
                log_data('refreshing' if sighup_refresh else '.')

            # update LCD message (NOT ON REFRESH)
            if secs_elapsed >= task_at_secs['update_lcd_content']:
                update_lcd_content(True)

        except (KeyboardInterrupt, SystemExit):
            # cleanup sensors & LCD
            sensor.cleanup()
            lcd.cleanup()
            ambient.reset()
            io_status.set_ambient(ambient)
            raise
        except Exception:
            log_stderr(traceback.format_exc())
            log_data('EXC: {}'.format(traceback.format_exc()))
        finally:
            # program change message
            if is_program_changed:
                say('', say_status=True)

            # stop refreshing cycle, reset status and program change
            sighup_refresh = is_status_changed = is_program_changed = False

            # update scheduled tasks (skip any lost task)
            for task in task_every_secs.keys():
                while secs_elapsed >= task_at_secs[task]:
                    task_at_secs[task] += task_every_secs[task]

            for task in task_every_mins.keys():
                if datetime.datetime.now().minute == task_at_mins[task]:
                    task_at_mins[task] += task_every_mins[task]
                    while task_at_mins[task] >= 60:
                        task_at_mins[task] -= 60

            # sync ambient
            ambient.update()
            io_status.set_ambient(ambient)

            try:
                # update lcd screen to 1 sec approx.
                cycle_duration = (datetime.datetime.now() - cycle_start_time)\
                    .total_seconds()
                for loop in range(4):
                    # catch command "interrupt" (jump to new cycle)
                    if sig_command:
                        break
                    frame_duration = lcd.update(io_status)
                    if frame_duration < .25 and cycle_duration < 1:
                        time.sleep(.25 - frame_duration)
                    cycle_duration += .25

                if sig_command:
                    sig_command = False
                    sighup_refresh = True

            except (KeyboardInterrupt, SystemExit):
                # cleanup sensors & LCD
                sensor.cleanup()
                lcd.cleanup()
                ambient.reset()
                io_status.set_ambient(ambient)
                raise
            except Exception:
                # LCD I/O error: refresh LCD screen
                log_stderr(traceback.format_exc())
                log_stderr('LCD I/O error: trying to recover..')
                time.sleep(1)
                lcd.refresh_display(io_status)


# initialize DB, I/O, signal handlers, tasks, message
def init():
    global temp, initial_time, sig_switch_timeout

    # migrate DB
    db.migrate()

    # SIGHUP & SIGTERM handlers definition
    signal.signal(signal.SIGHUP, sighup_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    # initialize output
    init_output()

    # initialize test mode
    if config.TEST_MODE > 0:
        io_status.ext_temp_c = 6.0
        io_status.req_temp_desc = 'Economy'
        io_status.heating_status = 'off'
        temp = TEST_INIT_TEMP

    initial_time = datetime.datetime.now()

    # reset scheduled tasks
    for task in task_every_secs.keys():
        task_at_secs[task] = 0

    for task in task_every_mins.keys():
        task_at_mins[task] = math.ceil(
            datetime.datetime.now().minute / task_every_mins[task]) \
                             * task_every_mins[task]
        while task_at_mins[task] >= 60:
            task_at_mins[task] -= 60

    # reset message
    io_status.reset_message()


def meteo():
    meteo_data = sensor.get_meteo()
    try:
        if meteo_data:
            io_status.place = io_status.weather = ''
            io_status.ext_temp_c = io_status.humidity = 0
            io_status.pressure = io_status.wind = 0.0

            io_status.place = meteo_data['name']
            if len(meteo_data['weather']) > 0:
                io_status.weather = meteo_data['weather'][0]['main']
            io_status.ext_temp_c = meteo_data['main']['temp']
            io_status.humidity = meteo_data['main']['humidity']
            io_status.pressure = meteo_data['main']['pressure']
            io_status.wind = meteo_data['wind']['speed']
        else:
            # occurs too often: just show a small mark on app (DISABLED!)
            if False and ' (*)' not in io_status.place:
                io_status.place += ' (*)'
    except (KeyError, ValueError):
        io_status.place = 'Error fetching meteo'
        log_stderr(traceback.format_exc())
        log_data('METEOEXC: {}'.format(traceback.format_exc()))


def aphorism():
    aphorism_data = sensor.get_aphorism()
    try:
        if aphorism_data:
            io_status.aphorism_text = aphorism_data['quoteText'].strip()
            io_status.aphorism_author = aphorism_data['quoteAuthor'].strip()
        else:
            # just show a small mark on app (DISABLED!)
            if False and io_status.aphorism_text \
                    and ' (*)' not in io_status.aphorism_text:
                io_status.aphorism_text += ' (*)'
    except Exception:
        io_status.aphorism_text = 'Error fetching aphorism'
        log_stderr(traceback.format_exc())
        log_data('APHOEXC: {}'.format(traceback.format_exc()))


def get_temperature():
    global temp
    global temp_avg_accu, temp_avg_counter, temp_avg_sum
    global log_temp_avg_accu, log_temp_avg_counter, log_temp_avg_sum
    # get temperature (moving average)
    # temperature is sampled n times ('get_temp'): each read is accumulated
    # in temp_avg_accu, with progressive weights (temp * n),
    # so more recent reads have priority.
    # At 'update_io' average temp is logged.
    if config.TEST_MODE > 0:
        temp += -10 * TEST_DELTA_EXT_INT_FACTOR
        if io_status.heating_status == 'on' or \
                io_status.heating_status == 'warming':
            temp += TEST_DELTA_THERMO_ON_TEMP_C
            # sensors delay test
            time.sleep(random.uniform(.0, .2))
    else:
        temp = sensor.read_temp()
    # skip wrong reads (null or > 50°C)
    if not temp or temp > 50.0:
        log_stderr('Temp sensor error: received {}'.format(temp))
    else:
        # accumulate temperature read
        temp_avg_counter += 1 + (.5 / task_every_secs['update_io'] /
                                 task_every_secs['get_temp'])
        temp_avg_sum += temp_avg_counter
        temp_avg_accu += temp * temp_avg_counter
        log_temp_avg_counter = 1
        log_temp_avg_sum += log_temp_avg_counter
        log_temp_avg_accu += temp * log_temp_avg_counter
        log_stdout('HOMPI', 'Req: {:.2f}° - Int: {:.2f}° - Thermo: {}'.format(
            io_status.req_temp_c, temp, io_status.heating_status))


def compute_status():
    global sig_switch_timeout, io_status

    current_time = datetime.datetime.now()

    slave_heating_on = False
    for slave_id, slave in io_status.hompi_slaves.items():
        slave_heating_on |= slave['heating_status'] == 'warming' or slave[
            'heating_status'] == 'on'

    if io_status.int_temp_c:
        last_change = dateutil.parser.parse(io_status.last_change)
        # print(current_time - last_change).total_seconds()

        if io_status.req_temp_c - io_status.int_temp_c >= \
                config.HEATING_THRESHOLD or slave_heating_on:
            if io_status.heating_status == 'off' or \
                    io_status.heating_status == 'cooling':
                # log_data('heating ON')
                io_status.last_change = current_time.isoformat()
                io_status.heating_status = 'warming'
                if config.TEST_MODE == 0:
                    sensor.set_heating(True)
            elif io_status.heating_status == 'warming' and \
                    (current_time - last_change).total_seconds() / 60.0 > \
                    config.THERMO_CHANGE_MINS:
                io_status.last_change = current_time.isoformat()
                io_status.heating_status = 'on'
        # *** stop heating on exact temp! ***
        if io_status.int_temp_c - io_status.req_temp_c >= 0 and \
                not slave_heating_on:
            if io_status.heating_status == 'on' or \
                    io_status.heating_status == 'warming':
                # log_data('heating OFF')
                io_status.last_change = current_time.isoformat()
                io_status.heating_status = 'cooling'
                if config.TEST_MODE == 0:
                    sensor.set_heating(False)
            elif io_status.heating_status == 'cooling' and \
                    (current_time - last_change).total_seconds() / 60.0 > \
                    config.THERMO_CHANGE_MINS:
                io_status.last_change = current_time.isoformat()
                io_status.heating_status = 'off'
    else:
        io_status.int_temp_c = 0

    # switch management
    for sw in range(len(config.BUTTONS)):
        if io_status.sw_sig[sw]:
            io_status.sw_sig[sw] = False
            io_status.sw_status[sw] = True
            sig_switch_timeout[sw] = current_time + datetime.timedelta(
                seconds=config.BUTTON_DURATION_SECS)
            io_status.last_change = current_time.isoformat()
            sensor.set_switch(config.BUTTONS[sw][0], True)

        if io_status.sw_status[sw] and current_time >= sig_switch_timeout[sw]:
            io_status.sw_status[sw] = False
            io_status.last_change = current_time.isoformat()
            sensor.set_switch(config.BUTTONS[sw][0], False)

    io_status.update(current_time)

    return io_status.last_change == current_time.isoformat()


def sighup_handler(signal, frame):
    global sig_command
    sig_command = True


def sigterm_handler(signal, frame):
    log_stdout('HOMPI', 'got SIGTERM - exiting.', LOG_INFO)
    log_data('stop')
    sys.exit(0)


def refresh_program(time_):
    global current_status, is_program_changed

    dbmgr = db.DatabaseManager()

    # refresh heating program
    row = dbmgr.query(
        """SELECT
            ttb.id, ttb.description, ttb.short_description,
            monday, tuesday, wednesday, thursday, friday, saturday, sunday,
            pre_holiday, holiday
        FROM gm_control AS ctl
        INNER JOIN gm_timetable AS ttb ON ttb.id = ctl.timetable_id""")\
        .fetchone()

    if holiday_list.get(datetime.datetime.today()):
        # today is a holiday
        day_type = row[11]
    elif holiday_list.get(
            datetime.datetime.today() + datetime.timedelta(days=1)):
        # today is a pre-holiday
        day_type = row[10]
    else:
        # normal day
        day_type = row[datetime.datetime.today().weekday() + 3]

    if io_status.mode_id != row[0]:
        io_status.mode_id = row[0]
        io_status.mode_desc = io_status.timetable_desc = row[1]
        io_status.short_mode_desc = row[2].upper()[0:1]
        is_program_changed = True
        log_stdout('HOMPI', 'Timetable: {} ({})'.format(io_status.mode_desc,
                                          io_status.short_mode_desc))
        sensor.hompi_slaves_forward_command(io_status.hompi_slaves,
                                            'TT={}'.format(row[0]))

    row = dbmgr.query(
        """SELECT
            tdata.orderby, tdtype.description, time_hhmm, delta_calc_mm,
            temp.description, temp_c
        FROM gm_timetable_day_type AS tdtype
        INNER JOIN gm_timetable_type_data AS tdata
            ON tdata.day_type_id = tdtype.id
        INNER JOIN gm_temp AS temp
            ON temp.id = tdata.temp_id
        WHERE tdtype.id = {:d}
        AND time_hhmm <= {:d}
        ORDER BY orderby DESC""".format(day_type, time_)
    ).fetchone()

    if io_status.day_type_desc != row[1] or \
            io_status.req_temp_c != row[5] or \
            io_status.req_start_time != row[2] or \
            io_status.req_temp_desc != row[4]:
        orderby = row[0]
        io_status.day_type_desc = row[1]
        io_status.req_temp_c = row[5]
        io_status.req_start_time = row[2]
        io_status.req_temp_desc = row[4]
        is_program_changed = True
        log_stdout('HOMPI', 'Day: {}({:02d}:{:02d}) - Temp({}): {:.2f}°'.format(
            row[1], datetime.datetime.today().hour,
            datetime.datetime.today().minute, row[4], row[5]))

        # get next change
        row = dbmgr.query(
            """SELECT
                time_hhmm, delta_calc_mm
            FROM gm_timetable_day_type AS tdtype
            INNER JOIN gm_timetable_type_data AS tdata
                ON tdata.day_type_id = tdtype.id
            INNER JOIN gm_temp AS temp
                ON temp.id = tdata.temp_id
            WHERE tdtype.id = {:d}
            AND tdata.orderby > {:d}
            ORDER BY orderby""".format(day_type, orderby)
        ).fetchone()
        if row:
            io_status.req_end_time = row[0]
        else:
            io_status.req_end_time = 0000
        log_stdout('HOMPI', 'Time range: ({:02.0f}:{:02.0f}) - ({:02.0f}:{:02.0f})'.format(
            math.floor(io_status.req_start_time // 100),
            io_status.req_start_time - math.floor(
                io_status.req_start_time // 100) * 100,
            math.floor(io_status.req_end_time // 100),
            io_status.req_end_time - math.floor(
                io_status.req_end_time // 100) * 100
        ))

    # refresh temperatures
    rows = dbmgr.query("SELECT id, description, temp_c FROM gm_temp")
    if rows:
        io_system.temperatures.clear()
        for row in rows:
            io_system.temperatures.append(dict(id=row[0], description=row[1], temp_c=row[2]))

def update_lcd_content(change=False):
    if change:
        lcd.change_dashboard_program(io_status)

    lcd.update_content(io_status, change)


def init_output():
    dbmgr = db.DatabaseManager()
    dbmgr.query("""DELETE FROM `gm_output`""")
    dbmgr.query("""INSERT INTO `gm_output` (`id`,`data`) VALUES (0,null)""")


def update_output():
    global current_status

    # update status
    if current_status != io_status.get_output():
        dbmgr = db.DatabaseManager()
        io_status.current_image = resources.current_image(config.IMAGE_PATH)
        io_status.last_update = datetime.datetime.now().isoformat()
        current_status = io_status.get_output()
        dbmgr.query(
            """UPDATE gm_output
            SET data = '{}', last_update = strftime('%s','now')
            WHERE id = 0""".format(current_status.replace('\'', '\'\'')))
        log_stdout('HOMPI', 'output: ' + current_status.replace('\n', ''))
        if config.ENABLE_HASS_INTEGRATION:
            hass.publish_status(io_status, io_system, ambient)

        update_lcd_content(change=False)


def process_input():
    global sig_command, is_status_changed
    # OLD FORMAT:
    # TT=[timetable_id]    ### set current timetable
    # TEMP=[temp_id],[temp_c] ### set temperature
    # PROG_T=[timetable_id],[ [daytype_id],[daytype_id],[daytype_id],
    #        [daytype_id],[daytype_id],[daytype_id],[daytype_id] ]
    # NEW FORMAT:
    # { "command": "TT", "value": [temp_c] }
    # { "command": "TEMP", "arg": [temp_id], "value": [temp_c] }
    # { "command": "PROG_T", "arg": [timetable_id], "value": "......" }

    dbmgr = db.DatabaseManager()
    rows = dbmgr.query(
        """SELECT id, last_update, data FROM gm_input
        ORDER BY last_update""").fetchall()
    show_ack = False
    for row in rows:
        data = row[2]
        dbmgr.query(
            "DELETE FROM gm_input WHERE id = {:d}".format(row[0]))
        log_data('INPUT data: {}'.format(data))
        command = arg = value = None
        try:
            json_command = json.loads(data)
            command = str(json_command["command"]).upper()
            if "arg" in json_command:
                arg = str(json_command["arg"]).upper()
            if "value" in json_command:
                value = str(json_command["value"]).upper()
        except:
            command = arg = value = None
            parser = data.split('=')
            if len(parser) > 1:
                command = parser[0].upper()
                parser = parser[1].split(',')
                if len(parser) > 1:
                    arg = parser[0].upper()
                    value = parser[1].upper()
                else:
                    value = parser[0].upper()
            else:
                log_data('PARSERROR: {}'.format(data))
                show_message('PARSERROR: {}'.format(data))
                continue
        if command == 'TT':
            try:
                if int(value):
                    dbmgr.query('UPDATE gm_control SET timetable_id = ?',
                                (value,))
                    show_message('TT CHANGE', 'TT CHANGE: {}'.format(value))
                    say('Timetable change')
                    sig_command = show_ack = True
            except Exception as e:
                log_data('PARSERROR ({}): {}'.format(data, e))
        elif command == 'TEMP':
            try:
                if int(arg) and float(value):
                    dbmgr.query(
                        'UPDATE gm_temp SET temp_c = ? WHERE id = ?',
                        (value, arg))
                    sig_command = show_ack = True
                    show_message('TP CHANGE', 'TP CHANGE ({}): {}'.format(arg, value))
                    say('Temperature change: ' + value + ' degrees')
            except Exception as e:
                log_data('PARSERROR ({}): {}'.format(data, e))
        elif command == 'LCD':
            if value == '0':
                lcd.set_backlight(0,
                                  datetime.datetime.now() +
                                  datetime.timedelta(hours=4))
                say('Display off')
            else:
                show_message('LCD ON')
                say('Display on')
                lcd.set_backlight(1)
            show_ack = True
        elif command == 'MESSAGE':
            io_status.send_message(value)
            show_message('', 'MESSAGE: {}'.format(value))
            say('Message: {}'.format(value))
            is_status_changed = show_ack = True
        elif command == 'AMBIENT':
            try:
                if not arg:
                    arg = 'COLOR'
                if arg == 'COLOR':
                    ambient.set_ambient_color(
                        value,
                        datetime.datetime.now() +
                        datetime.timedelta(hours=4))
                    show_message('AMBIENT', 'AMBIENT COLOR: #{}'.format(value))
                    say('Ambient color')
                elif arg == 'COLOR_HS':
                    ambient.set_ambient_color_hs(
                        value,
                        datetime.datetime.now() +
                        datetime.timedelta(hours=4))
                    show_message('AMBIENT', 'AMBIENT COLOR_HS: #{}'.format(value))
                    say('Ambient color')
                elif arg == 'BRIGHTNESS':
                    ambient.set_ambient_brightness(value)
                    show_message('AMBIENT', 'AMBIENT BRIGHTNESS: #{}'.format(value))
                    say('Ambient brightness')
                elif arg == 'STATUS':
                    ambient.set_ambient_on_off(
                        value == 'ON',
                        datetime.datetime.now() +
                        datetime.timedelta(hours=4))
                    show_message('AMBIENT', 'AMBIENT STATUS: {}'.format(value))
                    say('Ambient status {}'.format(value))
                else:
                    try:
                        ambient.set_ambient_effect(arg, value,
                        datetime.datetime.now() +
                        datetime.timedelta(hours=4))
                        show_message('AMBIENT', 'AMBIENT {}'.format(arg))
                        say('Ambient effect')
                    except Exception as e:
                        log_data('PARSERROR ({}): {}'.format(data, e))
                io_status.set_ambient(ambient)
            except Exception as e:
                log_data('PARSERROR ({}): {}'.format(data, e))
        elif command == 'GATE':
            # execute gate only once per cycle, and not while another
            # is running
            if len(config.BUTTONS):
                gate_button_index = -1
                index = 0
                for button in config.BUTTONS:
                    if 'GATE' == button[1].upper():
                        gate_button_index = index
                        break
                    index += 1
                if gate_button_index > -1 and \
                        not io_status.sw_status[gate_button_index]:
                    io_status.send_switch_command(gate_button_index)
                    show_ack = True
                    show_message('GATE', 'GATE OPEN')
                    say('Gate open')
        elif command == 'BUTTON':
            try:
                button_no = int(value)
                # execute switch only once per cycle, and not while another
                # is running
                if button_no < len(config.BUTTONS)\
                        and not io_status.sw_status[button_no]:
                    io_status.send_switch_command(button_no)
                    show_ack = True
                    show_message('BUTTON{}'.format(button_no))
                    say('Function {}'.format(button_no))
            except Exception as e:
                log_data('PARSERROR ({}): {}'.format(data, e))
                show_message('', 'PARSERROR: {}'.format(data))
        else:
            log_data('NOTIMPLEMENTED: {}'.format(data))

        # show ambient ack
        if config.MODULE_AMBIENT and show_ack:
            ambient.ambient_ack()

        is_status_changed |= sig_command


def show_message(lcd_message, telegram_message=""):
    log_stdout('HOMPI', 'message: [{}] - {}'.format(lcd_message, telegram_message), LOG_INFO)
    if config.ENABLE_TELEGRAM:
        if telegram_message == "":
            telegram_message = lcd_message
        if telegram_message != "":
            telegram_message = "{}: {}".format(
                socket.gethostname(), telegram_message)
            os_async_command('telegram "' + telegram_message + '"')
    if lcd_message != "":
        lcd.show_command(lcd_message)


def say(message, say_status = False):
    if config.MODULE_SPEECH:
        message = 'HOMPI - ' + message \
            + (' - ' + io_status.get_status_text() if say_status else '')
        command = config.SPEECH_COMMAND.format(message) + ' &'
        log_stdout('HOMPI', 'saying: {}'.format(message), LOG_INFO)
        os.system(command)


def log_data(event):
    if not config.MODULE_DB_LOG:
        return

    try:
        description = ''
        if not event:
            event = 'null'
        else:
            if event == '.':
                # log all temperatures
                for id, data in io_status.hompi_slaves.items():
                    description += str(data['int_temp_c']) + ';'
            event = "'{}'".format(event.replace('\'', '\'\''))

        if not description:
            if config.TEST_MODE:
                description = "'{}'".format(
                    io_status.get_output().replace('\'', '\'\''))
            else:
                description = 'null'
        else:
            # remove last ; and add quotes
            description = "'{}'".format(description[:-1])

        dbmgr = db.DatabaseManager()
        dbmgr.query("""
            INSERT INTO gm_log
            (datetime, int_temp_c, ext_temp_c, req_temp_c, event, description)
            VALUES (strftime('%s','now'), {:f}, {:f}, {:f}, {}, {})
            """.format(io_status.int_temp_c, io_status.ext_temp_c,
                       io_status.req_temp_c, event, description))
        log_stdout('HOMPI', 'gm_log: {}'.format(event))
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        log_stderr('log_data error: {}'.format(e))
        time.sleep(1)


if __name__ == "__main__":
    main()
