#!/usr/bin/env bash

# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>
#
# Thin wrapper for source checkouts. Instance copies live under
# $HOMPI_HOME/scripts/hompid.sh (written by ``hompi init``).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HOMPI_HOME="${HOMPI_HOME:-$ROOT}"
export HOMPI_VENV="${HOMPI_VENV:-${VIRTUAL_ENV:-$ROOT/venv}}"

exec bash "$ROOT/src/hompi/data/hompid.sh" "$@"
