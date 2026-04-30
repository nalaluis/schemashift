"""Tests for schemashift.cli_history."""

from __future__ import annotations

import json
import argparse
import pytest
from unittest.mock import patch, MagicMock

from schemashift.cli_history import run_history
from schemashift.comparator import SchemaChange, ChangeType
from schemashift.differ_history import HistoryError


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "history_cmd": "record",
        "old": "old.json",
        "new": "new.json",
        "history_file": ".history.json",
        "label": "",
        "breaking_only": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_change(ct: ChangeType) -> SchemaChange:
    return SchemaChange(change_type=ct, table="t", column=None, detail="d")


def test_run_record_load_error_returns_2():
    from schemashift.loader import SchemaLoadError
    args = _args(history_cmd="record")
    with patch("schemashift.cli_history.load_schema_from_file", side_effect=SchemaLoadError("bad")):
        assert run_history(args) == 2


def test_run_record_success_returns_0(tmp_path):
    schema = {"tables": {}}
    args = _args(history_cmd="record", history_file=str(tmp_path / "h.json"))
    with patch("schemashift.cli_history.load_schema_from_file", return_value=schema), \
         patch("schemashift.cli_history.compare_schemas", return_value=[]):
        assert run_history(args) == 0


def test_run_show_history_error_returns_2():
    args = _args(history_cmd="show")
    with patch("schemashift.cli_history.query_history", side_effect=HistoryError("missing")):
        assert run_history(args) == 2


def test_run_show_outputs_json(tmp_path, capsys):
    args = _args(history_cmd="show", history_file=str(tmp_path / "h.json"))
    fake_entries = [{"label": "v1", "change_count": 0, "changes": []}]
    with patch("schemashift.cli_history.query_history", return_value=fake_entries):
        result = run_history(args)
    assert result == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed[0]["label"] == "v1"


def test_run_unknown_history_cmd_returns_1():
    args = _args(history_cmd="unknown_cmd")
    assert run_history(args) == 1
