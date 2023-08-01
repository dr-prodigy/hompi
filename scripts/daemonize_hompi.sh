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

# Set to true if flask debugger is run as web server (localhost:5000)
# (for production purposes better rely on a WSGI server)
run_flask_debugger=false

# set HOMPI_HOME to default, if not yet set
export HOMPI_HOME=/home/pi/hompi

# *** kill running daemons ***
echo Killing hompi server..
kill $(ps aux |grep '[b]in/hompi' | awk '{print $2}') 2>/dev/null

if [ "$run_flask_debugger" = true ] ; then
  echo Killing flask debugger
  kill $(ps aux |grep '[w]s_api' | awk '{print $2}') 2>/dev/null
fi

echo Moving to $HOMPI_HOME..
cd $HOMPI_HOME

# *** restart ***
# Enable virtualenv
echo Enabling virtualenv..
. venv/bin/activate

# Daemonize hompi (suppress logging)
echo Daemonizing hompi..
nohup ./hompi >/dev/null 2>>~/hompi_error.log&

if [ "$run_flask_debugger" = true ] ; then
  echo Starting flask debugger..
  nohup python ws_api.py >/dev/null&
fi