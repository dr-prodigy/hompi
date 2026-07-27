#!/bin/bash

# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>
#
# Install Hompi from a source checkout (venv + editable package + instance init).
# Usage:
#   ./scripts/install.sh           # runtime deps only (safe on non-Pi hosts)
#   ./scripts/install.sh --pi      # also install Raspberry Pi / GPIO extras
#
# PyPI / non-clone installs:
#   python3 -m venv venv && . venv/bin/activate
#   pip install "hompi[pi]"
#   hompi init --home /path/to/instance

set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
export HOMPI_HOME="${HOMPI_HOME:-$(pwd)}"

python3 -m venv venv
# shellcheck disable=SC1091
. venv/bin/activate

python -m pip install -U pip setuptools wheel
if [[ "${1:-}" == "--pi" ]]; then
  python -m pip install -e ".[pi]"
else
  python -m pip install -e .
fi

hompi init --home "$HOMPI_HOME" --venv "${VIRTUAL_ENV:-$HOMPI_HOME/venv}"

echo
echo "Installed hompi $(python -c 'import hompi; print(hompi.__version__)')"
echo "Console scripts: hompi, hompi-api"
echo "Start daemon: hompi   |   systemd: systemctl --user enable --now hompi.service"
