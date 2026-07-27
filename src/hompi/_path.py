# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""Locate the project root and YAML config file."""

from __future__ import annotations

import os
from pathlib import Path

_BOOTSTRAPPED = False
_PROJECT_ROOT = None


def ensure_runtime_paths():
    """Prefer the project root as cwd for relative ``db/`` / ``migrations/`` paths.

    Resolution order for the project root:
    1. ``HOMPI_HOME``
    2. directory containing ``HOMPI_CONFIG`` (if set)
    3. current working directory
    4. repository root inferred from this package (editable ``src/`` layout)
    """
    global _BOOTSTRAPPED, _PROJECT_ROOT
    if _BOOTSTRAPPED:
        return _PROJECT_ROOT

    root = _find_project_root()
    _PROJECT_ROOT = root
    if root is None:
        _BOOTSTRAPPED = True
        return None

    try:
        if os.path.isdir(root) and os.path.abspath(os.getcwd()) != root:
            os.chdir(root)
    except OSError:
        pass

    _BOOTSTRAPPED = True
    return root


def find_config_file():
    """Return the path to the active YAML config, or ``None``."""
    env_path = os.environ.get('HOMPI_CONFIG')
    if env_path:
        path = Path(env_path).expanduser()
        if path.is_file():
            return path.resolve()
        raise FileNotFoundError(f'HOMPI_CONFIG does not exist: {env_path}')

    root = ensure_runtime_paths() or Path.cwd()
    root = Path(root)
    for name in ('config.yaml', 'config.yml'):
        candidate = root / name
        if candidate.is_file():
            return candidate.resolve()
    return None


def _find_project_root():
    candidates = []
    env_home = os.environ.get('HOMPI_HOME')
    if env_home:
        candidates.append(env_home)

    env_config = os.environ.get('HOMPI_CONFIG')
    if env_config:
        candidates.append(str(Path(env_config).expanduser().resolve().parent))

    candidates.append(os.getcwd())

    # src/hompi/_path.py -> repo root (editable installs)
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.dirname(os.path.dirname(pkg_dir)))

    seen = set()
    for raw in candidates:
        if not raw:
            continue
        root = os.path.abspath(raw)
        if root in seen:
            continue
        seen.add(root)
        if _looks_like_project_root(root):
            return root
    return None


def _looks_like_project_root(root):
    markers = (
        'config.yaml',
        'config.yml',
        'config.sample.yaml',
        'pyproject.toml',
        'db',
        'res',
    )
    return any(os.path.exists(os.path.join(root, marker)) for marker in markers)
