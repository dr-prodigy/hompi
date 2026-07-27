# Copyright (C)2018-24 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>.

"""Package smoke tests."""

from importlib.metadata import entry_points

import hompi


def test_version_is_set():
    assert hompi.__version__
    assert hompi.__version__.startswith("2.")


def test_console_scripts_registered():
    eps = entry_points()
    try:
        scripts = eps.select(group="console_scripts")
    except AttributeError:  # pragma: no cover - Python < 3.10 compatibility
        scripts = eps.get("console_scripts", [])
    names = {ep.name for ep in scripts if ep.value.startswith("hompi.")}
    assert "hompi" in names
    assert "hompi-api" in names


def test_main_entrypoints_callable():
    from hompi.app import main
    from hompi.service import HompiService, main as service_main
    from hompi.api import main as api_main

    assert callable(main)
    assert callable(service_main)
    assert callable(api_main)
    assert HompiService is not None
