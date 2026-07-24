#!/bin/bash

# Copyright (C) Maurizio Montel (dr-prodigy)
# This file is part of hompi <https://github.com/dr-prodigy/hompi>.
#
# Foreground entrypoint for a single container: control daemon + uWSGI API.
# Both share HOMPI_HOME (SQLite + PID files under run/).
#
# Expect host nginx to proxy to the uwsgi socket (127.0.0.1:3031). Prefer
# network_mode: host (or publish 127.0.0.1:3031:3031) so nginx can reach it.

set -euo pipefail

export HOMPI_HOME="${HOMPI_HOME:-/app}"
# Skip virtualenv/daemonize/pidfile blocks in uwsgi.ini
export HOMPI_CONTAINER=1

cd "$HOMPI_HOME"

mkdir -p "$HOMPI_HOME/run" "$HOMPI_HOME/logs" "$HOMPI_HOME/db"

hompi_pid=""

_cleanup() {
  if [ -n "${hompi_pid}" ] && kill -0 "${hompi_pid}" 2>/dev/null; then
    kill -TERM "${hompi_pid}" 2>/dev/null || true
    wait "${hompi_pid}" 2>/dev/null || true
  fi
}

trap _cleanup EXIT INT TERM

echo "Starting hompi control daemon.."
hompi &
hompi_pid=$!

echo "Starting uWSGI API (foreground, socket 127.0.0.1:3031).."
exec uwsgi --ini uwsgi.ini
