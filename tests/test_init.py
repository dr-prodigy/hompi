# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

from pathlib import Path

from hompi.init import init_instance


def test_init_creates_layout(tmp_path, monkeypatch):
    home = tmp_path / 'instance'
    venv = tmp_path / 'venv'
    venv.mkdir()
    unit_root = tmp_path / 'xdg'
    monkeypatch.setenv('XDG_CONFIG_HOME', str(unit_root))

    summary = init_instance(home, venv, systemd=True, force_config=False)

    assert (home / 'logs').is_dir()
    assert (home / 'run').is_dir()
    assert (home / 'db').is_dir()
    assert (home / 'config.yaml').is_file()
    assert (home / 'config.sample.yaml').is_file()
    assert (home / 'scripts' / 'hompid.sh').is_file()
    assert (home / 'uwsgi.ini').is_file()
    assert 'venv' in (home / 'uwsgi.ini').read_text() or str(venv) in (
        home / 'uwsgi.ini'
    ).read_text()

    unit = unit_root / 'systemd' / 'user' / 'hompi.service'
    assert unit.is_file()
    text = unit.read_text()
    assert str(home) in text
    assert str(venv) in text
    assert summary['systemd_unit'] == str(unit)


def test_init_skips_existing_config(tmp_path, monkeypatch):
    home = tmp_path / 'instance'
    home.mkdir()
    (home / 'config.yaml').write_text('KEEP: true\n', encoding='utf-8')
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'xdg'))

    init_instance(home, None, systemd=False, force_config=False)
    assert (home / 'config.yaml').read_text(encoding='utf-8') == 'KEEP: true\n'

    init_instance(home, None, systemd=False, force_config=True)
    assert 'KEEP: true' not in (home / 'config.yaml').read_text(encoding='utf-8')


def test_cli_dispatches_init(tmp_path, monkeypatch):
    from hompi.cli import main

    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'xdg'))
    try:
        main(['init', '--home', str(tmp_path / 'h'), '--no-systemd'])
    except SystemExit as exc:
        assert exc.code == 0
    assert (tmp_path / 'h' / 'run').is_dir()
