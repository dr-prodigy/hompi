# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

import os
import signal

from hompi import pidfile


def test_write_read_remove_pid(tmp_path, monkeypatch):
    monkeypatch.setattr(pidfile, 'data_dir', lambda: tmp_path)
    path = pidfile.daemon_pid_path()
    assert path.parent == tmp_path / 'run'

    pidfile.write_pid(path, 4242)
    assert pidfile.read_pid(path) == 4242
    assert pidfile.pid_is_alive(os.getpid())
    assert not pidfile.pid_is_alive(999999999)

    pidfile.remove_pid(path)
    assert pidfile.read_pid(path) is None


def test_signal_pidfile(tmp_path, monkeypatch):
    monkeypatch.setattr(pidfile, 'data_dir', lambda: tmp_path)
    path = pidfile.daemon_pid_path()
    pidfile.write_pid(path, os.getpid())

    sent = []
    real_kill = os.kill

    def fake_kill(pid, sig):
        if sig == 0:
            return real_kill(pid, 0)
        sent.append((pid, sig))

    monkeypatch.setattr(os, 'kill', fake_kill)
    assert pidfile.signal_pidfile(path, signal.SIGHUP) is True
    assert sent == [(os.getpid(), signal.SIGHUP)]

    pidfile.write_pid(path, 999999999)
    assert pidfile.signal_pidfile(path, signal.SIGHUP) is False


def test_replace_pidfile_claims_current(tmp_path, monkeypatch):
    monkeypatch.setattr(pidfile, 'data_dir', lambda: tmp_path)
    path = pidfile.ambient_pid_path()
    pidfile.write_pid(path, 999999999)
    pidfile.replace_pidfile(path, signal.SIGTERM)
    assert pidfile.read_pid(path) == os.getpid()
