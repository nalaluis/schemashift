"""Tests for schemashift.cli_merger."""

import json
import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace

from schemashift.cli_merger import run_merger, add_merger_subcommand
from schemashift.comparator import SchemaChange, ChangeType


def _make_change(change_type=ChangeType.COLUMN_REMOVED, table="users",
                 column="email", breaking=True, detail=""):
    return SchemaChange(
        change_type=change_type,
        table=table,
        column=column,
        breaking=breaking,
        detail=detail,
    )


def test_run_merger_invalid_pair_format(capsys):
    args = Namespace(pairs=["no_colon_here"], format="text")
    result = run_merger(args)
    assert result == 2
    captured = capsys.readouterr()
    assert "Invalid pair format" in captured.out


def test_run_merger_load_error_returns_2(capsys):
    args = Namespace(pairs=["old.json:new.json"], format="text")
    with patch("schemashift.cli_merger.load_schema_from_file", side_effect=Exception("not found")):
        result = run_merger(args)
    assert result == 2
    captured = capsys.readouterr()
    assert "Failed to load" in captured.out


def test_run_merger_no_breaking_returns_0(capsys):
    non_breaking = _make_change(ChangeType.TABLE_ADDED, breaking=False)
    args = Namespace(pairs=["old.json:new.json"], format="text")
    with patch("schemashift.cli_merger.load_schema_from_file", return_value={"tables": {}}):
        with patch("schemashift.cli_merger.compare_schemas", return_value=[non_breaking]):
            result = run_merger(args)
    assert result == 0


def test_run_merger_breaking_returns_1(capsys):
    breaking = _make_change(ChangeType.COLUMN_REMOVED, breaking=True)
    args = Namespace(pairs=["old.json:new.json"], format="text")
    with patch("schemashift.cli_merger.load_schema_from_file", return_value={"tables": {}}):
        with patch("schemashift.cli_merger.compare_schemas", return_value=[breaking]):
            result = run_merger(args)
    assert result == 1


def test_run_merger_json_format_outputs_valid_json(capsys):
    args = Namespace(pairs=["old.json:new.json"], format="json")
    with patch("schemashift.cli_merger.load_schema_from_file", return_value={"tables": {}}):
        with patch("schemashift.cli_merger.compare_schemas", return_value=[]):
            run_merger(args)
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert isinstance(parsed, (list, dict))


def test_add_merger_subcommand_registers():
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_merger_subcommand(subparsers)
    args = parser.parse_args(["merge", "--pairs", "a.json:b.json"])
    assert hasattr(args, "func")
    assert args.func is not None
