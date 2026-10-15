# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""Path / package-data resolution tests."""

from pathlib import Path

from hompi import paths
from hompi import _path as path_mod
import hompi.migrations


def _reset_path_bootstrap():
    path_mod._BOOTSTRAPPED = False
    path_mod._PROJECT_ROOT = None


def test_migrations_dir_points_at_packaged_migrations():
    mig = paths.migrations_dir()
    assert mig.is_dir()
    assert (mig / '20161122173616_init.py').is_file()
    assert Path(hompi.migrations.__file__).resolve().parent == mig.resolve()


def test_migrations_dir_ignores_empty_hompi_home_override(tmp_path, monkeypatch):
    """Leftover empty ``$HOMPI_HOME/migrations`` must not hide packaged scripts."""
    home = tmp_path / 'instance'
    home.mkdir()
    (home / 'config.yaml').write_text('HOMPI_ID: Test\n', encoding='utf-8')
    empty = home / 'migrations'
    empty.mkdir()
    (empty / '__pycache__').mkdir()

    monkeypatch.setenv('HOMPI_HOME', str(home))
    _reset_path_bootstrap()

    mig = paths.migrations_dir()
    assert mig == Path(hompi.migrations.__file__).resolve().parent
    assert (mig / '20161122173616_init.py').is_file()


def test_migrations_dir_uses_hompi_home_override_with_scripts(tmp_path, monkeypatch):
    home = tmp_path / 'instance'
    home.mkdir()
    (home / 'config.yaml').write_text('HOMPI_ID: Test\n', encoding='utf-8')
    override = home / 'migrations'
    override.mkdir()
    script = override / '20990101120000_custom.py'
    script.write_text('def upgrade(conn):\n    pass\n\ndef downgrade(conn):\n    pass\n')

    monkeypatch.setenv('HOMPI_HOME', str(home))
    _reset_path_bootstrap()

    assert paths.migrations_dir() == override


def test_db_dir_under_data_home():
    db_dir = paths.db_dir()
    assert db_dir.name == 'db'
    assert db_dir.is_dir()
    assert paths.db_file().name == 'hompi.sqlite'


def test_resolve_under_data_keeps_glob():
    resolved = paths.resolve_under_data('./res/images/*.jpg')
    assert str(resolved).endswith('res/images/*.jpg')
