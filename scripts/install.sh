#!/bin/bash

# Copyright (C) 2018 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com> <maurizio.montel@gmail.com>
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

## install prerequisites - 20250703 - not required
## sudo apt-get install python3-pip
## sudo pip3 install virtualenv

# move to script directory
cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
# move up
cd ..
# create virtualenv, activate it, setup requirements
## 20250703 - replaced with venv
## python3 -m virtualenv venv
python3 -m venv venv
. venv/bin/activate
pip install -r requirements/requirements.txt
pip install -r requirements/requirements-pi.txt
