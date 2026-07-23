# Copyright (C)2018-24 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>.

"""Resolve Hompi data directories (config home, DB, migrations, media)."""

from __future__ import annotations

from pathlib import Path

from ._path import ensure_runtime_paths


def data_dir():
    """Writable project data root (``HOMPI_HOME`` / discovered root)."""
    root = ensure_runtime_paths()
    if root:
        return Path(root)
    return Path.cwd()


def db_dir():
    path = data_dir() / 'db'
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_file(name='hompi.sqlite'):
    return db_dir() / name


def res_dir():
    path = data_dir() / 'res'
    path.mkdir(parents=True, exist_ok=True)
    return path


def images_glob():
    """Default image glob under the data dir."""
    return str(res_dir() / 'images' / '*.jpg')


def migrations_dir():
    """Filesystem path to Caribou migrations.

    Prefers ``$HOMPI_HOME/migrations`` when present (override), otherwise the
    migrations shipped inside the ``hompi`` package.
    """
    override = data_dir() / 'migrations'
    if override.is_dir() and any(override.iterdir()):
        return override

    import hompi.migrations as migrations_pkg
    return Path(migrations_pkg.__file__).resolve().parent


def resolve_under_data(path):
    """Resolve a possibly-relative path against the data dir (keeps glob suffixes)."""
    text = str(path)
    p = Path(text)
    if p.is_absolute():
        return p
    if text.startswith('./'):
        text = text[2:]
    return data_dir() / text
