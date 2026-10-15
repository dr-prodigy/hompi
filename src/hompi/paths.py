# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

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


def _packaged_migrations_dir():
    """Directory of Caribou migrations shipped inside the ``hompi`` package."""
    import hompi.migrations as migrations_pkg

    return Path(migrations_pkg.__file__).resolve().parent


def _has_caribou_migrations(directory: Path) -> bool:
    """True if *directory* contains Caribou migration modules (not just junk)."""
    if not directory.is_dir():
        return False
    for path in directory.glob('*.py'):
        name = path.name
        if name == '__init__.py':
            continue
        # Caribou: UTC timestamp prefix, optional leading ``v``
        stem = name[:-3]
        if stem[:1] == 'v':
            stem = stem[1:]
        if len(stem) >= 14 and stem[:14].isdigit():
            return True
    return False


def migrations_dir():
    """Filesystem path to Caribou migrations.

    Prefers ``$HOMPI_HOME/migrations`` only when it contains real Caribou
    migration scripts. An empty leftover directory (or one with only
    ``__pycache__``) is ignored so packaged migrations under
    ``hompi.migrations`` (``src/hompi/migrations`` in a source tree) are used.
    """
    override = data_dir() / 'migrations'
    if _has_caribou_migrations(override):
        return override
    return _packaged_migrations_dir()


def resolve_under_data(path):
    """Resolve a possibly-relative path against the data dir (keeps glob suffixes)."""
    text = str(path)
    p = Path(text)
    if p.is_absolute():
        return p
    if text.startswith('./'):
        text = text[2:]
    return data_dir() / text
