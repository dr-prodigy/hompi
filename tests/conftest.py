# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""Ensure a YAML config exists before Hompi modules are imported."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "config.sample.yaml"
CONFIG = ROOT / "config.yaml"

os.environ.setdefault("HOMPI_HOME", str(ROOT))
if not CONFIG.exists():
    shutil.copy(SAMPLE, CONFIG)
