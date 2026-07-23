# Copyright (C)2018-24 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>.

"""hompi home automation package."""

from ._path import ensure_runtime_paths
from .hardware import ensure_hardware_stubs

ensure_runtime_paths()
ensure_hardware_stubs()

__version__ = "2.0.0a1"
