# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""Project path bootstrap tests."""

from pathlib import Path

import hompi._path as path_mod
from hompi._path import ensure_runtime_paths, find_config_file


ROOT = Path(__file__).resolve().parents[1]


def test_ensure_runtime_paths_uses_hompi_home(monkeypatch, tmp_path):
    sample = ROOT / "config.sample.yaml"
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "migrations").mkdir()

    monkeypatch.setenv("HOMPI_HOME", str(tmp_path))
    monkeypatch.setenv("HOMPI_CONFIG", str(cfg))
    monkeypatch.chdir(tmp_path)

    path_mod._BOOTSTRAPPED = False
    path_mod._PROJECT_ROOT = None
    try:
        root = ensure_runtime_paths()
        assert Path(root) == tmp_path.resolve()
        assert Path.cwd() == tmp_path.resolve()
        assert find_config_file() == cfg.resolve()
    finally:
        # Restore project root for any subsequent tests in this process
        path_mod._BOOTSTRAPPED = False
        path_mod._PROJECT_ROOT = None
        monkeypatch.setenv("HOMPI_HOME", str(ROOT))
        monkeypatch.delenv("HOMPI_CONFIG", raising=False)
        monkeypatch.chdir(ROOT)
        ensure_runtime_paths()
