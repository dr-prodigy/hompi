#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>
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

from flask import Blueprint
from flask import Flask
from flask import request
from flask import send_file
from werkzeug import exceptions

import traceback
import json
import signal
import hashlib
import os
import urllib.request
from PIL import Image

from .config import config

from . import db
from . import io_data
from . import paths
from . import pidfile

# Public URL prefix (same for Flask debug and lighttpd/nginx → uWSGI).
API_PREFIX = '/hompi'

app = Flask(__name__)
api = Blueprint('api', __name__, url_prefix=API_PREFIX)


class RestoreMountPrefixMiddleware:
    """Fold proxy mount prefix back into PATH_INFO for Blueprint routing.

    Front ends that mount at ``/hompi`` (lighttpd ``scgi.server``, nginx
    ``location /hompi``) often pass ``SCRIPT_NAME=/hompi`` and
    ``PATH_INFO=/_get_status``. Routes live under ``url_prefix=/hompi``, so
    rewrite to ``PATH_INFO=/hompi/_get_status`` and clear ``SCRIPT_NAME``.
    Standalone debug (full path already in PATH_INFO) is unchanged.
    """

    def __init__(self, wsgi_app, prefix=API_PREFIX):
        self.app = wsgi_app
        self.prefix = prefix.rstrip('/') or '/'

    def __call__(self, environ, start_response):
        script = (environ.get('SCRIPT_NAME') or '').rstrip('/')
        path = environ.get('PATH_INFO') or ''
        if script == self.prefix and not path.startswith(self.prefix):
            if not path.startswith('/'):
                path = '/' + path
            environ['PATH_INFO'] = self.prefix + path
            environ['SCRIPT_NAME'] = ''
        return self.app(environ, start_response)


app.wsgi_app = RestoreMountPrefixMiddleware(app.wsgi_app)

print('HOMPI WS')
print('========')
API_KEY = ''
try:
    # calculate API_KEY (MD5 hash), if required
    if config.API_KEY:
        m = hashlib.md5()
        m.update(config.API_KEY.encode('utf-8'))
        API_KEY = m.hexdigest().upper()
except Exception:
    pass


def _signal_server():
    """Ask the control daemon to refresh (SIGHUP via PID file)."""
    try:
        if not pidfile.signal_pidfile(pidfile.daemon_pid_path(), signal.SIGHUP):
            print('_signal_server(): hompi daemon PID file missing or stale')
    except OSError as exc:
        print('_signal_server(): {}'.format(exc))


def _check_sharedkey():
    if API_KEY:
        api_key = request.args.get('api_key', '').upper()
        if api_key == API_KEY:
            return True
        else:
            return False
    else:
        return True


def _get_remote_address(server):
    dbmgr = db.DatabaseManager()
    try:
        status = json.loads(
            dbmgr.query("SELECT data FROM gm_output").fetchone()[0])
        return status["hompi_slaves"][server]["address"]
    except Exception:
        print("_get_remote_address({}): error".format(server))
        print(traceback.format_exc())
        return None


# READER METHODS (GET)
@api.route('/_get_system_info', methods=['GET'])
def get_system_info():
    if not _check_sharedkey():
        return "Forbidden", 403

    return io_data.SystemInfo().get_output()


@api.route('/_get_status', methods=['GET'])
def get_status():
    if not _check_sharedkey():
        return "Forbidden", 403

    dbmgr = db.DatabaseManager()
    try:
        return dbmgr.query("SELECT data FROM gm_output").fetchone()[0]
    except Exception:
        print("get_status(): error")
        print(traceback.format_exc())
        return "Error", 500  # INTERNAL_SERVER_ERROR


@api.route('/_get_list/<data_list>', methods=['GET'])
@api.route('/_get_list/<data_list>/<key>', methods=['GET'])
def get_list(data_list, key=None):
    if not _check_sharedkey():
        return "Forbidden", 403

    list_table = ('gm_timetable' if data_list == 'timetable' else
                  ('gm_timetable_day_type' if data_list == 'daytype' else
                   ('gm_temp' if data_list == 'temp' else
                    ('gm_timetable_type_data' if data_list == 'typedata' else
                    'gm_control'))))

    try:

        dbmgr = db.DatabaseManager()
        if data_list == 'temp':
            if key:
                _key = int(key)
                cur = dbmgr.query("""
                    SELECT `{}`.*, `timetable_id` FROM `{}`
                    INNER JOIN `gm_timetable_temp` ON
                        `temp_id` = `gm_temp`.`id`
                    WHERE `gm_timetable_temp`.`timetable_id` = ?
                    ORDER BY `gm_temp`.`id`
                """.format(list_table, list_table), (_key,))
            else:
                cur = dbmgr.query("""
                    SELECT `{}`.*, `timetable_id` FROM `{}`
                    INNER JOIN `gm_timetable_temp` ON `temp_id` = `gm_temp`.`id`
                    ORDER BY `gm_temp`.`id`
                """.format(list_table, list_table))
        else:
            if key:
                _key = int(key)
                if data_list == 'typedata':
                    cur = dbmgr.query("""
                        SELECT * FROM {}
                        WHERE `day_type_id` = ?
                        ORDER BY `id`
                        """.format(list_table), (_key,))
                else:
                   cur = dbmgr.query("""
                        SELECT * FROM {}
                        WHERE `id` = ?
                        ORDER BY `id`
                        """.format(list_table), (_key,))
            else:
                cur = dbmgr.query(
                    "SELECT * FROM {} ORDER BY id".format(list_table))
        r = [dict((cur.description[i][0], value)
                  for i, value in enumerate(row)) for row in cur.fetchall()]
        # one = False
        # return json.dumps((r[0] if r else None) if one else r)
        return json.dumps(r)
    except Exception:
        print("get_list({},{}): error".format(data_list, key))
        print(traceback.format_exc())
        return "Error", 500  # INTERNAL_SERVER_ERROR


@api.route('/_get_temp_chart', methods=['GET'])
def get_temp_chart():
    if not _check_sharedkey():
        return "Forbidden", 403

    dbmgr = db.DatabaseManager()

    try:
        # , description
        cur = dbmgr.query(
            """
            SELECT
                datetime(datetime,'unixepoch') AS datetime,
                datetime AS datetime_epoch, int_temp_c,
            ext_temp_c, req_temp_c, description
            FROM gm_log
            WHERE event = '.'
            AND date(datetime,'unixepoch') > datetime(date('now','-7 day'))
            """
        )
        r = [dict((cur.description[i][0], value)
                  for i, value in enumerate(row)) for row in cur.fetchall()]
        # one = False
        # return json.dumps((r[0] if r else None) if one else r)
        return json.dumps(r)
    except Exception:
        print("get_temp_chart(): error")
        print(traceback.format_exc())
        return "Error", 500  # INTERNAL_SERVER_ERROR


@api.route('/_get_server_list', methods=['GET'])
def get_server_list():
    if not _check_sharedkey():
        return "Forbidden", 403

    dbmgr = db.DatabaseManager()
    try:
        status = json.loads(
            dbmgr.query("SELECT data FROM gm_output").fetchone()[0])
        return json.dumps(status["hompi_slaves"].keys())
    except Exception:
        print("get_server_list(): error")
        print(traceback.format_exc())
        return "Error", 500  # INTERNAL_SERVER_ERROR


@api.route('/_get_list2/<server>/<list>', methods=['GET'])
@api.route('/_get_list2/<server>/<list>/<key>', methods=['GET'])
def get_list2(server, list, key=None):
    if not _check_sharedkey():
        return "Forbidden", 403

    try:
        # get local list
        if server == "local":
            return get_list(list, key)

        api_key = request.args.get('api_key', '').upper()
        address = _get_remote_address(server)

        if key:
            return urllib.request.urlopen(
                "{}/hompi/_get_list/{}/{}?api_key={}".format(address,
                                                             list, key,
                                                             api_key),
                timeout=2
            ).read()
        else:
            return urllib.request.urlopen(
                "{}/hompi/_get_list/{}?api_key={}".format(address, list,
                                                          api_key),
                timeout=2
            ).read()
    except Exception:
        print("get_list2({},{},{}): error".format(server, list, key))
        print(traceback.format_exc())
        return "Error", 500  # INTERNAL_SERVER_ERROR


@api.route('/_get_image/<image_name>', methods=['GET'])
def get_image(image_name):
    if not _check_sharedkey():
        return "Forbidden", 403

    try:
        image_dir = str(paths.resolve_under_data(config.IMAGE_PATH).parent)
        filename = '{}/{}'.format(image_dir, image_name)
        thumb_filename = '{}/thumbs/{}'.format(image_dir, image_name)
        if not os.path.isfile(thumb_filename):
            try:
                image = Image.open(filename)
                image.thumbnail(config.THUMB_SIZE, Image.ANTIALIAS)
                image.save(thumb_filename, 'JPEG')
            except Exception:
                print("get_image({}): error".format(image_name))
                print(traceback.format_exc())
                return "Error", 500  # INTERNAL_SERVER_ERROR

        return send_file(thumb_filename)
    except Exception:
        print("get_image({}): error".format(image_name))
        print(traceback.format_exc())
        return "Error", 500  # INTERNAL_SERVER_ERROR


# UPDATE METHODS (GET/PUT)
@api.route('/_send_command', methods=['PUT'])
@api.route('/_send_command/<command>', methods=['GET'])
def send_command(command=None):
    _data = ''
    if not _check_sharedkey():
        return "Forbidden", 403

    try:
        _command = []
        if request.method == 'PUT':
            _data = request.get_data()
        elif request.method == 'GET':
            _command = json.loads(command)
            _data = _command['data']
        else:
            return "Method not allowed", 405

        dbmgr = db.DatabaseManager()
        # insert with de-bounce
        dbmgr.query("""
            INSERT INTO `gm_input`(`data`)
            SELECT ? WHERE NOT EXISTS
            (SELECT * FROM `gm_input` WHERE `data` = ?)
            """, (_data, _data))
        _signal_server()
        return "Ok", 200
    except exceptions.UnsupportedMediaType:
        return "Unsupported Media Type", 415
    except Exception:
        print("send_command({}): error".format(command))
        print(traceback.format_exc())
        return "Error", 400  # BAD_REQUEST


@api.route('/_set_control', methods=['PUT'])
@api.route('/_set_control/<data>', methods=['GET'])
def set_control(data=None):
    if not _check_sharedkey():
        return "Forbidden", 403
    try:
        _data = None
        if request.method == 'PUT':
            _data = request.get_json()
        elif request.method == 'GET':
            _data = json.loads(data)
        else:
            return "Method not allowed", 405

        dbmgr = db.DatabaseManager()
        _id = None
        if 'timetable_id' in _data:
            _id = int(_data['timetable_id'])
        elif 'timetable_desc' in _data:
            row = dbmgr.query("SELECT id FROM gm_timetable WHERE description = ?",
                        (_data['timetable_desc'],)).fetchone()
            if row and len(row) > 0:
                _id = row[0]

        if _id:
            dbmgr.query("UPDATE gm_control SET timetable_id = ?", (_id,))
            _signal_server()
            return "Ok", 200
        else:
            return "Error", 400  # BAD_REQUEST

    except exceptions.UnsupportedMediaType:
        return "Unsupported Media Type", 415
    except Exception:
        print("set_control({}): error".format(data))
        print(traceback.format_exc())
        return "Error", 400  # BAD_REQUEST


@api.route('/_set_temp/<data>', methods=['PUT', 'GET'])
def set_temp(data):
    _id = _temp_c = 0
    if not _check_sharedkey():
        return "Forbidden", 403
    try:
        _data = []
        if request.method == 'PUT':
            _data = request.get_json()
            _id = int(data)
        elif request.method == 'GET':
            _data = json.loads(data)
            _id = int(_data['id'])
        else:
            return "Method not allowed", 405
        _temp_c = float(_data['temp_c'])

        dbmgr = db.DatabaseManager()
        dbmgr.query("""UPDATE gm_temp SET temp_c = ?
            WHERE id = ?""", (_temp_c, _id))
        _signal_server()
        return "Ok", 200
    except exceptions.UnsupportedMediaType:
        return "Unsupported Media Type", 415
    except Exception:
        print("set_temp({}): error".format(data))
        print(traceback.format_exc())
        return "Error", 400  # BAD_REQUEST


@api.route('/_set_temp2/<server>/<data>', methods=['PUT', 'GET'])
def set_temp2(server, data=None):
    if not _check_sharedkey():
        return "Forbidden", 403

    try:
        _data = []
        if request.method == 'PUT':
            _data = request.get_json()
            _data['id'] = data
        elif request.method == 'GET':
            _data = data
        else:
            return "Method not allowed", 405

        # set local temp
        if server == "local":
            return set_temp(data)

        api_key = request.args.get('api_key', '').upper()
        address = _get_remote_address(server)

        return urllib.request.urlopen(
            "{}/hompi/_set_temp/{}?api_key={}".format(address, data,
                                                      api_key), timeout=2
        ).read()
        return "Ok", 200
    except exceptions.UnsupportedMediaType:
        return "Unsupported Media Type", 415
    except Exception:
        print("set_temp2({},{}): error".format(server, data))
        print(traceback.format_exc())
        return "Error", 400  # BAD_REQUEST


# TO DO
@api.route('/_set_timetable/<data_json>')
def set_timetable(data_json):
    if not _check_sharedkey():
        return "Forbidden", 403

    try:
        days = ['monday','tuesday','wednesday','thursday',
                'friday','saturday','sunday','pre_holiday',
                'holiday']
        _data = json.loads(data_json)
        _id = int(_data['id'])
        _day_type_id = int(_data['day_type_id'])

        dbmgr = db.DatabaseManager()
        if _data['day'] in days:
            dbmgr.query("""UPDATE gm_timetable
                SET {} = ?
                WHERE id = ?
                """.format(_data['day']),
                        (_day_type_id, _id))
        else:
            return "Error", 400  # BAD_REQUEST
    except Exception:
        print("set_timetable_data({}): error".format(data_json))
        print(traceback.format_exc())
        return "Error", 400  # BAD_REQUEST
    return "Ok"


@api.route('/_set_timetable_data/<data_json>')
def set_timetable_data(data_json):
    if not _check_sharedkey():
        return "Forbidden", 403

    try:
        _data = json.loads(data_json)
        dbmgr = db.DatabaseManager()
        first = True
        for _tt_item in _data:
            _orderby = int(_tt_item['orderby'])
            _temp_id = int(_tt_item['temp_id'])
            _time_hhmm = int(_tt_item['time_hhmm'])
            _day_type_id = int(_tt_item['day_type_id'])
            if first:
                first = False
                dbmgr.query("""DELETE FROM gm_timetable_type_data
                    WHERE day_type_id = ?""", (_tt_item['day_type_id'],))
            dbmgr.query("""INSERT INTO gm_timetable_type_data
                (orderby, temp_id, time_hhmm, day_type_id)
                VALUES(?,?,?,?)""",
                    (_orderby, _temp_id,
                     _time_hhmm, _day_type_id))
        _signal_server()
    except Exception:
        print("set_timetable_data({}): error".format(data_json))
        print(traceback.format_exc())
        return "Error", 400  # BAD_REQUEST
    return "Ok"


@api.route('/_refresh', methods=['GET'])
def refresh():
    try:
        if not _check_sharedkey():
            return "Forbidden", 403
        _signal_server()
    except Exception:
        print("_refresh(): error")
        print(traceback.format_exc())
        return "Error", 400  # BAD_REQUEST
    return "Ok"


app.register_blueprint(api)


def main():
    """Console entry point for ``hompi-api`` / ``python -m hompi.api``."""
    app.run(host='127.0.0.1', debug=True)


if __name__ == "__main__":
    main()
