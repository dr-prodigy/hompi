# Copyright (C)2018-24 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>.

"""Path / package-data resolution tests."""

from pathlib import Path

from hompi import paths
import hompi.migrations


def test_migrations_dir_points_at_packaged_migrations():
    mig = paths.migrations_dir()
    assert mig.is_dir()
    assert (mig / '20161122173616_init.py').is_file()
    assert Path(hompi.migrations.__file__).resolve().parent == mig.resolve()


def test_db_dir_under_data_home():
    db_dir = paths.db_dir()
    assert db_dir.name == 'db'
    assert db_dir.is_dir()
    assert paths.db_file().name == 'hompi.sqlite'


def test_resolve_under_data_keeps_glob():
    resolved = paths.resolve_under_data('./res/images/*.jpg')
    assert str(resolved).endswith('res/images/*.jpg')
