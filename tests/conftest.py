# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""Ensure a YAML config exists and database is migrated before tests run."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

try:
    import pytest
except ImportError:
    pytest = None

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "config.sample.yaml"
CONFIG = ROOT / "config.yaml"

os.environ.setdefault("HOMPI_HOME", str(ROOT))
if not CONFIG.exists():
    shutil.copy(SAMPLE, CONFIG)


def _ensure_test_database():
    import caribou
    from hompi import db, paths

    persistent = paths.db_file("hompi.sqlite")
    os.makedirs(persistent.parent, exist_ok=True)
    caribou.upgrade(str(persistent), str(paths.migrations_dir()))
    if getattr(db.config, "TMPFS_ENABLE", False):
        tmp_db = db._tmpfs_db_path()
        os.makedirs(os.path.dirname(tmp_db) or ".", exist_ok=True)
        caribou.upgrade(str(tmp_db), str(paths.migrations_dir()))


_ensure_test_database()


if pytest is not None:
    @pytest.fixture(scope="session", autouse=True)
    def ensure_test_database():
        """Ensure database schema is migrated for tests."""
        _ensure_test_database()

