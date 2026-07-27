# Copyright (C)2018-24 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>.

"""PID-file helpers for daemon / ambient process coordination.

Replaces fragile ``ps | grep`` lookups so Hompi works in containers and
under non-``bin/hompi`` entry points.
"""

from __future__ import annotations

import atexit
import os
import signal
from pathlib import Path

from .paths import data_dir

_DAEMON_NAME = 'hompi.pid'
_AMBIENT_NAME = 'led_effects.pid'


def run_dir():
    path = data_dir() / 'run'
    path.mkdir(parents=True, exist_ok=True)
    return path


def daemon_pid_path():
    return run_dir() / _DAEMON_NAME


def ambient_pid_path():
    return run_dir() / _AMBIENT_NAME


def write_pid(path, pid=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{}\n'.format(pid if pid is not None else os.getpid()),
                    encoding='utf-8')


def remove_pid(path):
    Path(path).unlink(missing_ok=True)


def read_pid(path):
    try:
        return int(Path(path).read_text(encoding='utf-8').strip())
    except (OSError, ValueError):
        return None


def pid_is_alive(pid):
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we cannot signal it
        return True
    except OSError:
        return False
    return True


def signal_pidfile(path, sig=signal.SIGHUP):
    """Send ``sig`` to the process recorded in ``path``. Return True if sent."""
    pid = read_pid(path)
    if not pid_is_alive(pid):
        return False
    os.kill(pid, sig)
    return True


def replace_pidfile(path, sig=signal.SIGTERM):
    """Kill any previous process for ``path``, then claim it for this process."""
    path = Path(path)
    old = read_pid(path)
    if old and old != os.getpid() and pid_is_alive(old):
        try:
            os.kill(old, sig)
        except OSError:
            pass
    write_pid(path)
    atexit.register(remove_pid, path)


def install_daemon_pidfile():
    """Write the main daemon PID and remove it on normal interpreter exit."""
    path = daemon_pid_path()
    write_pid(path)
    atexit.register(remove_pid, path)
    return path
