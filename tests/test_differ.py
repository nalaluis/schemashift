"""Tests for schemashift.differ module."""

import pytest
from schemashift.comparator import SchemaChange, ChangeType
from schemashift.differ import (
    is_breaking,
    format_change,
    format_diff,
    count_breaking,
)


def _make_change(change_type, table="users", detail=""):
    return SchemaChange(change_type=change_type, table=table, detail=detail)


def test_is_breaking_table_removed():
    change = _make_change(ChangeType.TABLE_REMOVED)
    assert is_breaking(change) is True


def test_is_breaking_column_removed():
    change = _make_change(ChangeType.COLUMN_REMOVED, detail="email")
    assert is_breaking(change) is True


def test_is_breaking_column_type_changed():
    change = _make_change(ChangeType.COLUMN_TYPE_CHANGED, detail="id: int -> varchar")
    assert is_breaking(change) is True


def test_is_not_breaking_table_added():
    change = _make_change(ChangeType.TABLE_ADDED)
    assert is_breaking(change) is False


def test_is_not_breaking_column_added():
    change = _make_change(ChangeType.COLUMN_ADDED, detail="nickname")
    assert is_breaking(change) is False


def test_format_change_breaking_prefix():
    change = _make_change(ChangeType.COLUMN_REMOVED, detail="age")
    result = format_change(change)
    assert result.startswith("[BREAKING]")


def test_format_change_non_breaking_prefix():
    change = _make_change(ChangeType.COLUMN_ADDED, detail="nickname")
    result = format_change(change)
    assert result.startswith("[non-breaking]")


def test_format_change_color_contains_ansi():
    change = _make_change(ChangeType.TABLE_REMOVED)
    result = format_change(change, color=True)
    assert "\033[" in result


def test_format_diff_no_changes():
    result = format_diff([])
    assert result == "No schema changes detected."


def test_format_diff_summary_line():
    changes = [
        _make_change(ChangeType.TABLE_REMOVED),
        _make_change(ChangeType.COLUMN_ADDED, detail="bio"),
    ]
    result = format_diff(changes)
    assert "2 change(s)" in result
    assert "1 breaking" in result


def test_count_breaking_mixed():
    changes = [
        _make_change(ChangeType.TABLE_REMOVED),
        _make_change(ChangeType.COLUMN_ADDED, detail="bio"),
        _make_change(ChangeType.COLUMN_REMOVED, detail="email"),
    ]
    assert count_breaking(changes) == 2


def test_count_breaking_none():
    changes = [_make_change(ChangeType.TABLE_ADDED)]
    assert count_breaking(changes) == 0
