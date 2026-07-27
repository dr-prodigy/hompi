# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""YAML configuration loader tests."""

from pathlib import Path

import pytest
import yaml

from hompi.config import Settings, load_settings
from hompi._path import find_config_file


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "config.sample.yaml"


def test_sample_yaml_is_valid_mapping():
    raw = yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    assert "HOMPI_ID" in raw
    assert raw["THERMOSTAT_MODE"] == 3
    assert raw["I2C_ADDRESS"] == 0x27


def test_load_settings_from_sample(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(SAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    settings = load_settings(cfg)
    assert settings.HOMPI_ID == "Living"
    assert settings.THERMOSTAT_MODE == 3
    assert settings.I2C_ADDRESS == 0x27
    assert settings.THUMB_SIZE == (800, 800)
    assert settings.BUTTONS[0] == [18, "Gate"]
    assert settings.API_KEY is None
    assert settings._config_path == str(cfg)


def test_load_settings_overrides(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "HOMPI_ID: Kitchen\nTHERMOSTAT_MODE: 1\nTHUMB_SIZE: [640, 480]\n",
        encoding="utf-8",
    )
    settings = load_settings(cfg)
    assert settings.HOMPI_ID == "Kitchen"
    assert settings.THERMOSTAT_MODE == 1
    assert settings.THUMB_SIZE == (640, 480)
    # Defaults still applied for omitted keys
    assert settings.MQTT_PORT == 1883


def test_settings_attribute_error():
    settings = Settings({"HOMPI_ID": "X"})
    with pytest.raises(AttributeError):
        _ = settings.DOES_NOT_EXIST


def test_find_config_file_discovers_project_config():
    path = find_config_file()
    assert path is not None
    assert path.name in {"config.yaml", "config.yml"}
