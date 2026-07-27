# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""Instance bootstrap: runtime dirs, sample config, uWSGI, systemd user unit."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
from importlib import resources
from pathlib import Path


def detect_venv() -> Path | None:
    env = os.environ.get('VIRTUAL_ENV')
    if env:
        return Path(env).resolve()
    base = getattr(sys, 'base_prefix', sys.prefix)
    if Path(sys.prefix).resolve() != Path(base).resolve():
        return Path(sys.prefix).resolve()
    return None


def default_home() -> Path:
    env = os.environ.get('HOMPI_HOME')
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd().resolve()


def _data_path(name: str) -> Path:
    return resources.files('hompi.data').joinpath(name)


def _read_data(name: str) -> str:
    return _data_path(name).read_text(encoding='utf-8')


def _write_text(path: Path, text: str, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    if mode is not None:
        path.chmod(mode)


def _virtualenv_ini_value(home: Path, venv: Path | None) -> str:
    """Value for uWSGI ``virtualenv =`` (absolute, or ``venv`` if under home)."""
    if venv is None:
        return 'venv'
    venv = venv.resolve()
    try:
        rel = venv.relative_to(home.resolve())
        if str(rel) == 'venv':
            return 'venv'
    except ValueError:
        pass
    return str(venv)


def init_instance(
    home: Path,
    venv: Path | None = None,
    *,
    systemd: bool = True,
    force_config: bool = False,
) -> dict:
    """Create a Hompi instance directory layout. Return a summary dict."""
    home = home.expanduser().resolve()
    if venv is None:
        venv = detect_venv()
    elif venv is not None:
        venv = Path(venv).expanduser().resolve()

    summary = {
        'home': str(home),
        'venv': str(venv) if venv else None,
        'created': [],
        'skipped': [],
        'systemd_unit': None,
    }

    for name in ('logs', 'run', 'db', 'res', 'scripts'):
        path = home / name
        path.mkdir(parents=True, exist_ok=True)
        summary['created'].append(str(path))

    # Sample → config.yaml
    config_path = home / 'config.yaml'
    if config_path.exists() and not force_config:
        summary['skipped'].append(str(config_path))
    else:
        _write_text(config_path, _read_data('config.sample.yaml'))
        summary['created'].append(str(config_path))

    # Also keep a local sample for editing/reference
    sample_path = home / 'config.sample.yaml'
    if not sample_path.exists() or force_config:
        _write_text(sample_path, _read_data('config.sample.yaml'))
        summary['created'].append(str(sample_path))
    else:
        summary['skipped'].append(str(sample_path))

    # Supervisor script
    hompid_dst = home / 'scripts' / 'hompid.sh'
    _write_text(
        hompid_dst,
        _read_data('hompid.sh'),
        mode=stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH,
    )
    summary['created'].append(str(hompid_dst))

    # uWSGI config
    uwsgi_dst = home / 'uwsgi.ini'
    uwsgi_text = _read_data('uwsgi.ini').replace(
        '@HOMPI_VENV@', _virtualenv_ini_value(home, venv)
    )
    if uwsgi_dst.exists() and not force_config:
        summary['skipped'].append(str(uwsgi_dst))
    else:
        _write_text(uwsgi_dst, uwsgi_text)
        summary['created'].append(str(uwsgi_dst))

    if systemd:
        unit_dir = Path(
            os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')
        ) / 'systemd' / 'user'
        unit_dir.mkdir(parents=True, exist_ok=True)
        unit_path = unit_dir / 'hompi.service'
        venv_str = str(venv) if venv else ''
        unit_text = (
            _read_data('hompi.service')
            .replace('@HOMPI_HOME@', str(home))
            .replace('@HOMPI_VENV@', venv_str)
        )
        _write_text(unit_path, unit_text)
        summary['systemd_unit'] = str(unit_path)
        summary['created'].append(str(unit_path))
        try:
            subprocess.run(
                ['systemctl', '--user', 'daemon-reload'],
                check=False,
                capture_output=True,
            )
        except OSError:
            pass

    return summary


def _print_summary(summary: dict) -> None:
    print('Hompi instance initialized')
    print('  HOMPI_HOME: {}'.format(summary['home']))
    print('  HOMPI_VENV: {}'.format(summary['venv'] or '(not set — use PATH / home/venv)'))
    if summary.get('systemd_unit'):
        print('  systemd unit: {}'.format(summary['systemd_unit']))
        print('  enable with: systemctl --user enable --now hompi.service')
    print('  edit config: {}/config.yaml'.format(summary['home']))


def build_init_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='hompi init',
        description='Bootstrap a Hompi instance (dirs, config, uWSGI, systemd).',
    )
    p.add_argument(
        '--home',
        default=None,
        help='Instance directory (default: $HOMPI_HOME or current directory)',
    )
    p.add_argument(
        '--venv',
        default=None,
        help='Virtualenv path for systemd/uWSGI (default: auto-detect)',
    )
    p.add_argument(
        '--systemd',
        dest='systemd',
        action='store_true',
        default=True,
        help='Install systemd --user unit (default)',
    )
    p.add_argument(
        '--no-systemd',
        dest='systemd',
        action='store_false',
        help='Skip systemd user unit',
    )
    p.add_argument(
        '--force',
        action='store_true',
        help='Overwrite config.yaml / uwsgi.ini if they already exist',
    )
    return p


def cmd_init(argv: list[str]) -> int:
    args = build_init_parser().parse_args(argv)
    home = Path(args.home) if args.home else default_home()
    venv = Path(args.venv) if args.venv else detect_venv()
    summary = init_instance(
        home,
        venv,
        systemd=args.systemd,
        force_config=args.force,
    )
    _print_summary(summary)
    return 0
