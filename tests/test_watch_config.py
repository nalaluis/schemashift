"""Tests for schemashift.watch_config."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schemashift.watch_config import load_watch_config, WatchConfigError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, data: dict) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return p


_VALID = {"baseline": "baseline.json", "schema": "schema.json"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_load_valid_json_config(tmp_path):
    p = _write(tmp_path, "watch.json", _VALID)
    cfg = load_watch_config(p)
    assert cfg["baseline"] == "baseline.json"
    assert cfg["schema"] == "schema.json"


def test_defaults_are_applied(tmp_path):
    p = _write(tmp_path, "watch.json", _VALID)
    cfg = load_watch_config(p)
    assert cfg["output_format"] == "text"
    assert cfg["fail_on_breaking"] is True


def test_custom_values_override_defaults(tmp_path):
    data = {**_VALID, "output_format": "markdown", "fail_on_breaking": False}
    p = _write(tmp_path, "watch.json", data)
    cfg = load_watch_config(p)
    assert cfg["output_format"] == "markdown"
    assert cfg["fail_on_breaking"] is False


def test_missing_file_raises(tmp_path):
    with pytest.raises(WatchConfigError, match="not found"):
        load_watch_config(tmp_path / "missing.json")


def test_invalid_json_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{bad json")
    with pytest.raises(WatchConfigError, match="Invalid JSON"):
        load_watch_config(p)


def test_missing_required_key_raises(tmp_path):
    p = _write(tmp_path, "watch.json", {"baseline": "b.json"})
    with pytest.raises(WatchConfigError, match="missing required keys"):
        load_watch_config(p)


def test_top_level_not_a_dict_raises(tmp_path):
    p = tmp_path / "watch.json"
    p.write_text(json.dumps(["baseline", "schema"]))
    with pytest.raises(WatchConfigError, match="mapping"):
        load_watch_config(p)


def test_unsupported_extension_raises(tmp_path):
    p = tmp_path / "watch.toml"
    p.write_text("")
    with pytest.raises(WatchConfigError, match="Unsupported config format"):
        load_watch_config(p)
