# Copyright (C)2018-24 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>.

"""Install hardware stub modules when real Pi drivers are unavailable.

Call :func:`ensure_hardware_stubs` early so ``import RPi.GPIO``, ``import smbus``,
and ``import spidev`` succeed on non-Pi hosts without cwd symlinks.
"""

from __future__ import annotations

import sys
import types


def ensure_hardware_stubs():
    """Register stub modules in ``sys.modules`` when native drivers are missing."""
    _ensure_rpi_gpio()
    from .stubs import smbus as smbus_stub
    from .stubs import spidev as spidev_stub
    _install_if_missing('smbus', smbus_stub)
    _install_if_missing('spidev', spidev_stub)


def _install_if_missing(top_name, stub_module):
    if top_name in sys.modules:
        return
    try:
        __import__(top_name)
    except ImportError:
        sys.modules[top_name] = stub_module


def _ensure_rpi_gpio():
    if 'RPi.GPIO' in sys.modules:
        return
    try:
        import RPi.GPIO  # noqa: F401
        return
    except ImportError:
        pass

    from .stubs.RPi import GPIO as gpio_mod

    rpi_pkg = sys.modules.get('RPi')
    if rpi_pkg is None:
        rpi_pkg = types.ModuleType('RPi')
        rpi_pkg.__path__ = []
        sys.modules['RPi'] = rpi_pkg
    sys.modules['RPi.GPIO'] = gpio_mod
    rpi_pkg.GPIO = gpio_mod
