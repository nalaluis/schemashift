"""Tests for schemashift.differ_history."""

from __future__ import annotations

import json
import os
import pytest

from schemashift.comparator import SchemaChange, ChangeType
from schemashift.differ_history import (
    HistoryError,
    record_entry,
    load_history,
    query_history,
)


def _make(ct: ChangeType, table: str = "users", column: str | None = None) -> SchemaChange:
    return SchemaChange(change_type=ct, table=table, column=column, detail="test")


def test_record_entry_creates_file(tmp_path):
    path = str(tmp_path / "history.json")
    changes = [_make(ChangeType.TABLE_REMOVED)]
    entry = record_entry(path, changes, label="v1")
    assert os.path.exists(path)
    assert entry["change_count"] == 1
    assert entry["label"] == "v1"


def test_record_entry_appends(tmp_path):
    path = str(tmp_path / "history.json")
    record_entry(path, [_make(ChangeType.TABLE_REMOVED)], label="v1")
    record_entry(path, [_make(ChangeType.COLUMN_ADDED)], label="v2")
    history = load_history(path)
    assert len(history) == 2
    assert history[0]["label"] == "v1"
    assert history[1]["label"] == "v2"


def test_record_entry_empty_changes(tmp_path):
    path = str(tmp_path / "history.json")
    entry = record_entry(path, [])
    assert entry["change_count"] == 0
    assert entry["changes"] == []


def test_load_history_file_not_found(tmp_path):
    with pytest.raises(HistoryError, match="not found"):
        load_history(str(tmp_path / "missing.json"))


def test_load_history_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("not json")
    with pytest.raises(HistoryError, match="Invalid JSON"):
        load_history(str(path))


def test_load_history_not_a_list(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"key": "value"}))
    with pytest.raises(HistoryError, match="array"):
        load_history(str(path))


def test_query_history_filter_by_label(tmp_path):
    path = str(tmp_path / "history.json")
    record_entry(path, [_make(ChangeType.TABLE_REMOVED)], label="release-1")
    record_entry(path, [_make(ChangeType.COLUMN_ADDED)], label="release-2")
    results = query_history(path, label="release-1")
    assert len(results) == 1
    assert results[0]["label"] == "release-1"


def test_query_history_breaking_only(tmp_path):
    path = str(tmp_path / "history.json")
    record_entry(path, [_make(ChangeType.COLUMN_ADDED)], label="safe")
    record_entry(path, [_make(ChangeType.TABLE_REMOVED)], label="dangerous")
    results = query_history(path, breaking_only=True)
    assert len(results) == 1
    assert results[0]["label"] == "dangerous"


def test_query_history_no_filters_returns_all(tmp_path):
    path = str(tmp_path / "history.json")
    for i in range(3):
        record_entry(path, [_make(ChangeType.TABLE_ADDED)], label=f"v{i}")
    results = query_history(path)
    assert len(results) == 3
