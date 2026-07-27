# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""hompi home automation package."""

from ._path import ensure_runtime_paths
from .hardware import ensure_hardware_stubs

ensure_runtime_paths()
ensure_hardware_stubs()

__version__ = "2.0.0a1"
