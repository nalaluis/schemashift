"""Tests for schemashift.snapshotter."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from schemashift.snapshotter import (
    SnapshotError,
    take_snapshot,
    save_snapshot,
    load_snapshot,
    diff_snapshots,
    snapshot_metadata,
)


def _schema(tables: dict | None = None) -> dict:
    return {"tables": tables or {}}


def _simple_table() -> dict:
    return {"columns": {"id": {"type": "integer"}}, "indexes": {}}


# --- take_snapshot ---

def test_take_snapshot_returns_metadata():
    snap = take_snapshot(_schema(), label="v1")
    assert snap["label"] == "v1"
    assert snap["snapshot_version"] == 1
    assert "captured_at" in snap
    assert "schema" in snap


def test_take_snapshot_captured_at_is_recent():
    before = time.time()
    snap = take_snapshot(_schema())
    after = time.time()
    assert before <= snap["captured_at"] <= after


def test_take_snapshot_invalid_schema_raises():
    with pytest.raises(SnapshotError, match="Invalid schema"):
        take_snapshot({"not_valid": True})


# --- save / load roundtrip ---

def test_save_and_load_roundtrip(tmp_path):
    snap = take_snapshot(_schema({"users": _simple_table()}), label="test")
    dest = tmp_path / "snap.json"
    save_snapshot(snap, dest)
    loaded = load_snapshot(dest)
    assert loaded["label"] == "test"
    assert loaded["schema"]["tables"]["users"] == _simple_table()


def test_save_creates_parent_dirs(tmp_path):
    snap = take_snapshot(_schema())
    dest = tmp_path / "nested" / "dir" / "snap.json"
    save_snapshot(snap, dest)
    assert dest.exists()


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot(tmp_path / "missing.json")


def test_load_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    with pytest.raises(SnapshotError):
        load_snapshot(bad)


def test_load_missing_schema_key_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"label": "x"}))
    with pytest.raises(SnapshotError, match="Invalid snapshot format"):
        load_snapshot(bad)


# --- diff_snapshots ---

def test_diff_snapshots_no_changes():
    schema = _schema({"users": _simple_table()})
    old = take_snapshot(schema)
    new = take_snapshot(schema)
    assert diff_snapshots(old, new) == []


def test_diff_snapshots_detects_table_removed():
    old = take_snapshot(_schema({"users": _simple_table()}))
    new = take_snapshot(_schema({}))
    changes = diff_snapshots(old, new)
    assert any(c.change_type.name == "TABLE_REMOVED" for c in changes)


def test_diff_snapshots_missing_schema_key_raises():
    with pytest.raises(SnapshotError, match="Missing 'schema'"):
        diff_snapshots({"label": "x"}, take_snapshot(_schema()))


# --- snapshot_metadata ---

def test_snapshot_metadata_fields():
    snap = take_snapshot(_schema(), label="release-1")
    meta = snapshot_metadata(snap)
    assert meta["label"] == "release-1"
    assert meta["snapshot_version"] == 1
    assert "captured_at" in meta
    assert "schema" not in meta
