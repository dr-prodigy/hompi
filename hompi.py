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
import io_data
import sensors
import dashboard
import resources
import ambient
import random

import socket

from tendo import singleton
from utils import log_stderr, os_async_command

io_status = io_data.Status()
sensor = sensors.Sensors()
lcd = dashboard.Dashboard()
ambient = ambient.Ambient()

TEST_INIT_TEMP = 20.0
TEST_DELTA_EXT_INT_COEFF = .001
TEST_DELTA_THERMO_ON_TEMP_C = .03
current_status = ''
sig_command = False
is_status_changed = True

initial_time = datetime.datetime.now()
sig_switch_timeout = [datetime.datetime.now()]*len(config.BUTTONS)

temp = temp_avg_accu = temp_avg_sum = 0.0
temp_avg_counter = 0
log_temp_avg_accu = log_temp_avg_sum = 0.0
log_temp_avg_counter = 0

try:
    if config.HOLIDAYS_COUNTRY:
        holiday_list = holidays.CountryHoliday(config.HOLIDAYS_COUNTRY)
    else:
        print("WARN: config.HOLIDAYS_COUNTRY missing, defaulting to IT")
        holiday_list = holidays.IT()
except Exception:
    print("WARN: config.HOLIDAYS_COUNTRY missing or wrong, defaulting to IT")
    holiday_list = holidays.IT()

task_every_secs = {
    'hompi_slaves_refresh': 31.0,
    'update_lcd_content': 21.0,
    'get_temp': 4.0,
    'get_meteo': 300.0,  # 5 mins
    'get_aphorism': 241.0,  # 4 mins
    'refresh': 304.0,  # 5 mins (multiple of get_temp)
    'update_temp': 40.0,
    'update_io': 10.0,
}

task_every_mins = {
    'log': 15.0
}

task_at_secs = {}
task_at_mins = {}

refreshing = True


def main():
    global sig_command, refreshing, is_status_changed, lcd
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
                refreshing = True

            # OPERATIONS NOT DONE ON REFRESH - START
            # update hompiS
            if secs_elapsed >= task_at_secs['hompi_slaves_refresh']:
                sensor.hompi_slaves_refresh(io_status.hompi_slaves)

            # update I/O: meteo
            if secs_elapsed >= task_at_secs['get_meteo'] \
                    and config.MODULE_METEO:
                meteo()

            # aphorism
            if secs_elapsed >= task_at_secs['get_aphorism'] \
                    and config.MODULE_APHORISM:
                aphorism()

            # re-sync things
            if secs_elapsed >= task_at_secs['refresh']:
                # ambient color
                if config.MODULE_AMBIENT:
                    io_status.current_ambient_color = ambient.ambient_refresh()
                # temp sensor failure: reset temp sampling
                if config.MODULE_TEMP and temp_avg_sum == 0:
                    temp_avg_accu = temp_avg_counter = 0.0
                    io_status.int_temp_c = 0.0
            # OPERATIONS NOT DONE ON REFRESH - END

            # update I/O (ack occurring here gets ambient control)
            if secs_elapsed >= task_at_secs['update_io'] or refreshing:
                process_input()

            # get temperature
            if (secs_elapsed >= task_at_secs[
                    'get_temp'] or refreshing) and config.MODULE_TEMP:
                get_temperature()

            # update temperature
            if (secs_elapsed >= task_at_secs[
                    'update_temp'] or refreshing):
                # save new temperature (if valid)
                if temp_avg_sum != 0:
                    io_status.int_temp_c = \
                        round(temp_avg_accu / temp_avg_sum, 2)
                # reset temp sampling
                temp_avg_accu = temp_avg_counter = temp_avg_sum = 0

            # refresh program
            if secs_elapsed >= task_at_secs['refresh'] or refreshing:
                refresh_program(current_time)

            # compute status (heating, switches, ...)
            is_status_changed |= compute_status()

            # update I/O: output
            if secs_elapsed >= task_at_secs['update_io'] or \
                    refreshing or is_status_changed:
                update_output()

            # log data (check task_at_mins)
            if (datetime.datetime.now().minute == task_at_mins[
                'log'] or refreshing) \
                    and log_temp_avg_sum > 0:
                io_status.int_temp_c = round(
                    log_temp_avg_accu / log_temp_avg_sum, 2)
                log_temp_avg_accu = log_temp_avg_counter = log_temp_avg_sum = 0
                log_data('refreshing' if refreshing else '.')

            # update LCD message (NOT ON REFRESH)
            if secs_elapsed >= task_at_secs['update_lcd_content']:
                update_lcd_content()

            # status speech
            if is_status_changed and config.MODULE_SPEECH:
                command = config.SPEECH_COMMAND.format(
                    io_status.get_status_text()) + ' &'
                print('status changed: executing {}'.format(command))
                os.system(command)

        except (KeyboardInterrupt, SystemExit):
            # cleanup sensors & LCD
            sensor.cleanup()
            lcd.cleanup()
            ambient.cleanup()
            raise
        except Exception:
            log_stderr(traceback.format_exc())
            log_data('EXC: {}'.format(traceback.format_exc()))
        finally:
            # stop refreshing cycle, reset status change
            refreshing = is_status_changed = False

            # update scheduled tasks (skip any lost task)
            for task in task_every_secs.keys():
                while secs_elapsed >= task_at_secs[task]:
                    task_at_secs[task] += task_every_secs[task]

            for task in task_every_mins.keys():
                if datetime.datetime.now().minute == task_at_mins[task]:
                    task_at_mins[task] += task_every_mins[task]
                    while task_at_mins[task] >= 60:
                        task_at_mins[task] -= 60

            # sync ambient color
            io_status.current_ambient_color = ambient.update()

            try:
                # update lcd screen to 1 sec approx.
                cycle_duration = (datetime.datetime.now() - cycle_start_time)\
                    .total_seconds()
                while cycle_duration < 1:
                    # catch command "interrupt" (jump to new cycle)
                    if sig_command:
                        break
                    frame_duration = lcd.update(io_status)
                    if frame_duration < .25:
                        time.sleep(.25 - frame_duration)
                    cycle_duration += .25

                if sig_command:
                    sig_command = False
                    refreshing = True

            except (KeyboardInterrupt, SystemExit):
                # cleanup sensors & LCD
                sensor.cleanup()
                lcd.cleanup()
                ambient.cleanup()
                raise
            except Exception:
                # LCD I/O error: refresh LCD screen
                log_stderr(traceback.format_exc())
                log_stderr('LCD I/O error: trying to recover..')
                time.sleep(1)
                lcd = dashboard.Dashboard()


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
        io_data.init_test(io_status)
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
    meteo = sensor.get_meteo()
    try:
        if meteo:
            io_status.place = io_status.weather = ''
            io_status.ext_temp_c = io_status.humidity = 0
            io_status.pressure = io_status.wind = 0.0

            io_status.place = meteo['name']
            if len(meteo['weather']) > 0:
                io_status.weather = meteo['weather'][0]['main']
            io_status.ext_temp_c = meteo['main']['temp']
            io_status.humidity = meteo['main']['humidity']
            io_status.pressure = meteo['main']['pressure']
            io_status.wind = meteo['wind']['speed']
        else:
            # occurs too often: just show a small mark on app
            if (' (*)' not in io_status.place):
                io_status.place += ' (*)'
    except (KeyError, ValueError):
        io_status.place = 'Error fetching meteo'
        log_stderr(traceback.format_exc())
        log_data('METEOEXC: {}'.format(traceback.format_exc()))


def aphorism():
    aphorism = sensor.get_aphorism()
    try:
        if aphorism:
            io_status.aphorism_text = aphorism['quoteText'].strip()
            io_status.aphorism_author = aphorism['quoteAuthor'].strip()
        else:
            # just show a small mark on app
            if (io_status.aphorism_text and
                    ' (*)' not in io_status.aphorism_text):
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
        temp += -10 * TEST_DELTA_EXT_INT_COEFF
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
        print('Req: {:.2f}° - Int: {:.2f}° - Thermo: {}'.format(
            io_status.req_temp_c, temp, io_status.heating_status))


def compute_status():
    global sig_switch_timeout, io_status

    current_time = datetime.datetime.now()

    slave_heating_on = False
    for id, slave in io_status.hompi_slaves.items():
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

        if io_status.sw_status[sw] and current_time > sig_switch_timeout[sw]:
            io_status.sw_status[sw] = False
            io_status.last_change = current_time.isoformat()
            sensor.set_switch(config.BUTTONS[sw][0], False)

    io_status.update(current_time)

    return io_status.last_change == current_time.isoformat()


def sighup_handler(signal, frame):
    global sig_command
    sig_command = True


def sigterm_handler(signal, frame):
    print('got SIGTERM - exiting.')
    log_data('stop')
    sys.exit(0)


def refresh_program(time_):
    global current_status

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
    io_status.mode_id = row[0]
    io_status.mode_desc = io_status.timetable_desc = row[1]
    io_status.short_mode_desc = row[2].upper()[0:1]
    print('Timetable: {} ({})'.format(io_status.mode_desc,
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
    orderby = row[0]
    io_status.day_type_desc = row[1]
    io_status.req_temp_c = row[5]
    io_status.req_start_time = row[2]
    io_status.req_temp_desc = row[4]
    print('Day: {}({:02d}:{:02d}) - Temp({}): {:.2f}°'.format(
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
    print('Time range: ({:02.0f}:{:02.0f}) - ({:02.0f}:{:02.0f})'.format(
        math.floor(io_status.req_start_time // 100),
        io_status.req_start_time - math.floor(
            io_status.req_start_time // 100) * 100,
        math.floor(io_status.req_end_time // 100),
        io_status.req_end_time - math.floor(
            io_status.req_end_time // 100) * 100
    ))


def update_lcd_content(change=True):
    if change:
        lcd.change_dashboard_program(io_status)

    lcd.update_content(io_status, change)


def init_output():
    dbmgr = db.DatabaseManager()
    dbmgr.query("""DELETE FROM `gm_output`""")
    dbmgr.query("""INSERT INTO `gm_output` (`id`,`data`) VALUES (0,null)""")


def update_output():
    global current_status

    dbmgr = db.DatabaseManager()

    # update status
    if current_status != io_status.get_output():
        io_status.current_image = resources.current_image(config.IMAGE_PATH)
        io_status.last_update = datetime.datetime.now().isoformat()
        dbmgr.query(
            """UPDATE gm_output
            SET data = '{}', last_update = strftime('%s','now')
            WHERE id = 0""".format(
                io_status.get_output().replace('\'', '\'\'')))
        current_status = io_status.get_output()
        print('OUTPUT: ' + current_status.replace('\n', ''))

        update_lcd_content(change=False)


def process_input():
    global sig_command, is_status_changed
    # TT=[timetable_id]    ### set current timetable
    # TEMP=[temp_id],[temp_c] ### set temperature
    # PROG_T=[timetable_id],[ [daytype_id],[daytype_id],[daytype_id],
    #        [daytype_id],[daytype_id],[daytype_id],[daytype_id] ]

    dbmgr = db.DatabaseManager()
    rows = dbmgr.query(
        """SELECT id, last_update, data FROM gm_input
        ORDER BY last_update""").fetchall()
    show_ack = False
    for row in rows:
        _command = row[2]

        dbmgr = db.DatabaseManager()
        dbmgr.query(
            "DELETE FROM gm_input WHERE id = {:d}".format(row[0]))
        parser = _command.split('=')
        log_data('command: {}'.format(_command))
        if len(parser) > 1:
            if parser[0].upper() == 'TT':
                try:
                    if (int(parser[1])):
                        dbmgr.query('UPDATE gm_control SET timetable_id = ?',
                                    (parser[1]))
                        show_message('TT CHANGE')
                        sig_command = show_ack = True
                except Exception:
                    log_data('PARSERROR: {}'.format(_command))
            elif parser[0].upper() == 'TEMP':
                try:
                    parser2 = parser[1].split(',')
                    if int(parser2[0]) and flssoat(parser2[1]):
                        dbmgr.query(
                            'UPDATE gm_temp SET temp_c = ? WHERE id = ?',
                            (parser2[1], parser2[0]))
                        sig_command = show_ack = True
                        show_message('TP CHANGE')
                except Exception as e:
                    log_data('PARSERROR: {}'.format(_command))
            elif parser[0].upper() == 'LCD':
                if parser[1] == '0':
                    lcd.set_backlight(0,
                                      datetime.datetime.now() +
                                      datetime.timedelta(hours=4))
                else:
                    show_message('LCD ON')
                    lcd.set_backlight(1)
                show_ack = True
            elif parser[0].upper() == 'MESSAGE':
                io_status.send_message(parser[1])
                is_status_changed = True
                show_ack = True
            elif parser[0].upper() == 'AMBIENT' or \
                    parser[0].upper() == 'AMBIENT_COLOR':
                try:
                    if config.MODULE_AMBIENT:
                        io_status.current_ambient_color = \
                            ambient.set_ambient_crossfade(
                                parser[1],
                                datetime.datetime.now() +
                                datetime.timedelta(hours=4))
                        show_message('COLOR', 'AMBIENT COLOR ' + parser[1])
                except Exception as e:
                    log_data('PARSERROR: {}\n{}'.format(
                            _command,
                            traceback.format_exc()))
            elif parser[0].upper() == 'AMBIENT_XMAS':
                try:
                    if config.MODULE_AMBIENT:
                        ambient.set_ambient_xmas_daisy(parser[1])
                        show_message('COLOR', 'AMBIENT XMAS')
                except Exception as e:
                    log_data('PARSERROR: {}\n{}'.format(
                            _command,
                            traceback.format_exc()))
            elif parser[0].upper() == 'GATE':
                # execute gate only once per cycle, and not while another
                # is running
                if len(config.BUTTONS) and not io_status.sw_status[0]:
                    # assume gate is 1st switch
                    io_status.send_switch_command(0)
                    show_ack = True
                    show_message('GATE', 'GATE OPEN')
            elif parser[0].upper() == 'BUTTON':
                try:
                    button_no = int(parser[1])
                    # execute switch only once per cycle, and not while another
                    # is running
                    if button_no < len(config.BUTTONS)\
                            and not io_status.sw_status[button_no]:
                        io_status.send_switch_command(button_no)
                        show_ack = True
                        show_message('BUTTON' + button_no)
                except Exception as e:
                    log_data('PARSERROR: {}\n{}'.format(
                        _command,
                        traceback.format_exc()))
            else:
                log_data('NOTIMPLEMENTED: {}'.format(_command))
        else:
            log_data('PARSERROR: {}'.format(_command))

        # show ambient ack
        if config.MODULE_AMBIENT and show_ack:
            ambient.ambient_ack()

        is_status_changed |= sig_command


def show_message(lcd_message, telegram_message=""):
    if config.ENABLE_TELEGRAM:
        if telegram_message == "":
            telegram_message = lcd_message
        telegram_message = socket.gethostname() + ": " + telegram_message
        os_async_command('telegram "' + telegram_message + '"')
    lcd.show_command(lcd_message)


def log_data(event):
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
            if config.VERBOSE_LOG:
                description = "'{}'".format(
                    io_status.get_output().replace('\'', '\'\''))
            else:
                description = 'null'
        else:
            # remove last ; and add quotes
            description = "'{}'".format(description[:-1])

        if not config.MODULE_DB_LOG:
            return

        dbmgr = db.DatabaseManager()
        dbmgr.query("""
            INSERT INTO gm_log
            (datetime, int_temp_c, ext_temp_c, req_temp_c, event, description)
            VALUES (strftime('%s','now'), {:f}, {:f}, {:f}, {}, {})
            """.format(io_status.int_temp_c, io_status.ext_temp_c,
                       io_status.req_temp_c, event, description))
        print('Logged data: {}'.format(event))
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        log_stderr('log_data error: {}'.format(traceback.format_exc()))
        time.sleep(1)

if __name__ == "__main__":
    main()
