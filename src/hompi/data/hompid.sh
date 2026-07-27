#!/bin/bash

# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>
#
# Hompi process supervisor (control daemon + optional uWSGI / Flask API).
# Usage: hompid.sh {start|stop|restart}
#
# Environment:
#   HOMPI_HOME  Instance data directory (config, db, logs, run, uwsgi.ini)
#   HOMPI_VENV  Optional absolute path to the Python virtualenv

run_uwsgi=true
run_flask_debugger=false

export HOMPI_HOME="${HOMPI_HOME:-/home/pi/hompi}"

_kill_pidfile() {
  local pidfile="$1"
  if [ -f "$pidfile" ]; then
    kill "$(cat "$pidfile")" 2>/dev/null || true
    rm -f "$pidfile"
  fi
}

_activate() {
  cd "$HOMPI_HOME"
  if [ -n "${HOMPI_VENV:-}" ] && [ -f "$HOMPI_VENV/bin/activate" ]; then
    # shellcheck disable=SC1091
    . "$HOMPI_VENV/bin/activate"
  elif [ -f "$HOMPI_HOME/venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    . "$HOMPI_HOME/venv/bin/activate"
  fi
  export HOMPI_HOME
  mkdir -p "$HOMPI_HOME/logs" "$HOMPI_HOME/run"
}

do_stop() {
  echo "Stopping hompi server.."
  _kill_pidfile "$HOMPI_HOME/run/hompi.pid"
  # Legacy fallbacks (pre-PID-file installs)
  kill $(ps aux |grep '[v]env/bin/hompi' |grep -v 'hompi-api' | awk '{print $2}') 2>/dev/null || true
  kill $(ps aux |grep '[b]in/hompi' |grep -v 'hompi-api' | awk '{print $2}') 2>/dev/null || true

  _activate

  if [ "$run_uwsgi" = true ] ; then
    echo "Stopping uWSGI API.."
    if [ -f "$HOMPI_HOME/run/uwsgi-hompi-api.pid" ] ; then
      uwsgi --stop "$HOMPI_HOME/run/uwsgi-hompi-api.pid" 2>/dev/null || true
    fi
    # Legacy pid location (pre-run/ move)
    if [ -f "$HOMPI_HOME/logs/uwsgi-hompi-api.pid" ] ; then
      uwsgi --stop "$HOMPI_HOME/logs/uwsgi-hompi-api.pid" 2>/dev/null || true
    fi
    kill $(ps aux |grep '[u]wsgi.*uwsgi.ini' | awk '{print $2}') 2>/dev/null || true
    while [ -e "$HOMPI_HOME/run/uwsgi-hompi-api.pid" ] || \
          [ -e "$HOMPI_HOME/logs/uwsgi-hompi-api.pid" ]; do
      sleep 0.2
    done
    echo "uWSGI fully stopped"
  fi

  if [ "$run_flask_debugger" = true ] ; then
    echo "Stopping flask debugger.."
    kill $(ps aux |grep '[v]env/bin/hompi-api' | awk '{print $2}') 2>/dev/null || true
    kill $(ps aux |grep '[h]ompi.api' | awk '{print $2}') 2>/dev/null || true
  fi
}

do_start() {
  _activate

  echo "Starting hompi.."
  nohup hompi >/dev/null 2>>"$HOMPI_HOME/logs/hompi_error.log" &

  if [ "$run_uwsgi" = true ] ; then
    echo "Starting uWSGI API.."
    # daemonize/pidfile/log/socket/virtualenv are set in uwsgi.ini
    uwsgi --ini "$HOMPI_HOME/uwsgi.ini"
  fi

  if [ "$run_flask_debugger" = true ] ; then
    echo "Starting flask debugger.."
    nohup hompi-api >/dev/null &
  fi
}

do_restart() {
  do_stop
  do_start
}

usage() {
  echo "Usage: $0 {start|stop|restart}" >&2
  exit 1
}

case "${1:-}" in
  start)   do_start ;;
  stop)    do_stop ;;
  restart) do_restart ;;
  *)       usage ;;
esac
