"""Tests for schemashift.watcher."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schemashift.watcher import watch, WatcherError, WatchResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _schema(tables: dict) -> dict:
    return {"tables": tables}


def _simple_table(columns: dict | None = None, indexes: dict | None = None) -> dict:
    return {"columns": columns or {}, "indexes": indexes or {}}


def _write_baseline(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "baseline.json"
    p.write_text(json.dumps(data))
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_watch_no_changes(tmp_path):
    schema = _schema({"users": _simple_table({"id": {"type": "int"}})})
    baseline_path = _write_baseline(tmp_path, schema)

    result = watch(baseline_path, schema)

    assert isinstance(result, WatchResult)
    assert result.is_clean
    assert result.breaking_count == 0
    assert result.changes == []


def test_watch_detects_column_removed(tmp_path):
    old = _schema({"users": _simple_table({"id": {"type": "int"}, "name": {"type": "varchar"}})})
    new = _schema({"users": _simple_table({"id": {"type": "int"}})})
    baseline_path = _write_baseline(tmp_path, old)

    result = watch(baseline_path, new)

    assert result.has_changes
    assert result.breaking_count >= 1


def test_watch_detects_table_removed(tmp_path):
    old = _schema({"orders": _simple_table({"id": {"type": "int"}})})
    new = _schema({})
    baseline_path = _write_baseline(tmp_path, old)

    result = watch(baseline_path, new)

    assert result.has_changes
    assert result.breaking_count >= 1


def test_watch_non_breaking_addition(tmp_path):
    old = _schema({"users": _simple_table({"id": {"type": "int"}})})
    new = _schema({"users": _simple_table({"id": {"type": "int"}, "email": {"type": "varchar"}})})
    baseline_path = _write_baseline(tmp_path, old)

    result = watch(baseline_path, new)

    assert result.has_changes
    assert result.breaking_count == 0


def test_watch_missing_baseline_raises(tmp_path):
    schema = _schema({})
    with pytest.raises(WatcherError, match="Could not load baseline"):
        watch(tmp_path / "nonexistent.json", schema)


def test_watch_invalid_baseline_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json")
    with pytest.raises(WatcherError):
        watch(bad, _schema({}))


def test_watch_result_baseline_path_recorded(tmp_path):
    schema = _schema({})
    baseline_path = _write_baseline(tmp_path, schema)

    result = watch(baseline_path, schema)

    assert result.baseline_path == str(baseline_path)
