#!/bin/bash

# Copyright (C) Maurizio Montel (dr-prodigy)
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

# Production API: uWSGI (uwsgi.ini). Dev-only Flask debugger is opt-in.
run_uwsgi=true
run_flask_debugger=false

# set HOMPI_HOME to default, if not yet set
export HOMPI_HOME="${HOMPI_HOME:-/home/pi/hompi}"

# *** kill running daemons ***
echo Killing hompi server..
# Console script from the venv (and legacy bin/hompi if still present)
kill $(ps aux |grep '[v]env/bin/hompi' |grep -v 'hompi-api' | awk '{print $2}') 2>/dev/null
kill $(ps aux |grep '[b]in/hompi' |grep -v 'hompi-api' | awk '{print $2}') 2>/dev/null

echo Moving to $HOMPI_HOME..
cd "$HOMPI_HOME"

# Enable virtualenv early so uwsgi stop/start use the venv binary
echo Enabling virtualenv..
# shellcheck disable=SC1091
. venv/bin/activate

export HOMPI_HOME
mkdir -p logs

if [ "$run_uwsgi" = true ] ; then
  echo Stopping uWSGI API..
  if [ -f logs/uwsgi-hompi-api.pid ] ; then
    uwsgi --stop logs/uwsgi-hompi-api.pid 2>/dev/null || true
  fi
  kill $(ps aux |grep '[u]wsgi.*uwsgi.ini' | awk '{print $2}') 2>/dev/null || true
fi

if [ "$run_flask_debugger" = true ] ; then
  echo Killing flask debugger
  kill $(ps aux |grep '[v]env/bin/hompi-api' | awk '{print $2}') 2>/dev/null
  kill $(ps aux |grep '[h]ompi.ws_api' | awk '{print $2}') 2>/dev/null
fi

# *** restart ***
echo Daemonizing hompi..
nohup hompi >/dev/null 2>>~/hompi_error.log&

if [ "$run_uwsgi" = true ] ; then
  echo Starting uWSGI API..
  # daemonize/pidfile/log are set in uwsgi.ini
  uwsgi --ini uwsgi.ini
fi

if [ "$run_flask_debugger" = true ] ; then
  echo Starting flask debugger..
  nohup hompi-api >/dev/null&
fi
