#!/bin/bash

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

# Install hompi into a local venv (editable).
# Usage:
#   ./scripts/install.sh           # runtime deps only (safe on non-Pi hosts)
#   ./scripts/install.sh --pi      # also install Raspberry Pi / GPIO extras

set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
export HOMPI_HOME="${HOMPI_HOME:-$(pwd)}"

mkdir -p "$HOMPI_HOME/logs" "$HOMPI_HOME/run"
# logs/: uWSGI / daemon stderr logs; run/: process PID files (hompi, uWSGI, LED)

SYSTEMD_USER_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"
sed "s|@HOMPI_HOME@|${HOMPI_HOME}|g" \
  "$HOMPI_HOME/scripts/hompi.service" \
  > "$SYSTEMD_USER_DIR/hompi.service"
echo "Installed user unit: $SYSTEMD_USER_DIR/hompi.service"
if command -v systemctl >/dev/null 2>&1; then
  systemctl --user daemon-reload || true
fi

python3 -m venv venv
# shellcheck disable=SC1091
. venv/bin/activate

python -m pip install -U pip setuptools wheel
python -m pip install -e .

if [[ "${1:-}" == "--pi" ]]; then
  python -m pip install -e ".[pi]"
fi

echo
echo "Installed hompi $(python -c 'import hompi; print(hompi.__version__)')"
echo "Runtime dirs: $HOMPI_HOME/logs , $HOMPI_HOME/run"
echo "systemd (user): systemctl --user enable --now hompi.service"
echo "Next: cp config.sample.yaml config.yaml && . venv/bin/activate && hompi"
echo "Console scripts: hompi, hompi-api"
