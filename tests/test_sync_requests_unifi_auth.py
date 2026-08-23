"""Unit tests for requests-unifi-auth sync helper (no live PyPI)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync_requests_unifi_auth.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("sync_requests_unifi_auth", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sync_mod():
    return _load_module()


def test_read_dep_floor_and_project_version(sync_mod):
    text = (
        'version = "0.1.3"\n'
        "dependencies = [\n"
        '    "requests-unifi-auth>=0.1.5",\n'
        "]\n"
        'current_version = "0.1.3"\n'
    )
    assert sync_mod.read_dep_floor(text) == "0.1.5"
    assert sync_mod.read_project_version(text) == "0.1.3"


def test_bump_patch(sync_mod):
    assert sync_mod.bump_patch("0.1.3") == "0.1.4"
    assert sync_mod.bump_patch("1.0.0") == "1.0.1"


def test_apply_updates(sync_mod):
    pyproject = (
        'version = "0.1.3"\n'
        "dependencies = [\n"
        '    "click>=8.0.0",\n'
        '    "requests-unifi-auth>=0.1.5",\n'
        "]\n"
        'current_version = "0.1.3"\n'
    )
    init = '__version__ = "0.1.3"\n'
    new_py, new_init = sync_mod.apply_updates(
        pyproject_text=pyproject,
        init_text=init,
        new_dep_version="0.2.0",
        new_package_version="0.1.4",
    )
    assert 'requests-unifi-auth>=0.2.0"' in new_py
    assert 'version = "0.1.4"' in new_py
    assert 'current_version = "0.1.4"' in new_py
    assert new_init == '__version__ = "0.1.4"\n'
