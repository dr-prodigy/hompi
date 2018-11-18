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

# move to script directory
cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
# Enable virtualenv
cd ..
. venv/bin/activate

# Start hompi in background (no logging)
nohup ./hompi >/dev/null 2>>~/hompi_error.log&

# Uncomment next line to run flask debugger as server (localhost:5000)
# (for production purposes better rely on a WSGI server)
# nohup python ws_api.py >/dev/null&
