"""Tests for schemashift.grouper."""

import pytest

from schemashift.comparator import ChangeType, SchemaChange
from schemashift.grouper import (
    GrouperError,
    group_by_change_type,
    group_by_severity,
    group_by_table,
    group_summary,
)


def _make(change_type: ChangeType, table: str = "users", column: str = "id") -> SchemaChange:
    return SchemaChange(change_type=change_type, table=table, column=column)


def test_group_by_table_empty():
    assert group_by_table([]) == {}


def test_group_by_table_single_table():
    changes = [_make(ChangeType.COLUMN_REMOVED), _make(ChangeType.COLUMN_TYPE_CHANGED)]
    result = group_by_table(changes)
    assert "users" in result
    assert len(result["users"]) == 2


def test_group_by_table_multiple_tables():
    changes = [
        _make(ChangeType.COLUMN_REMOVED, table="users"),
        _make(ChangeType.TABLE_REMOVED, table="orders"),
    ]
    result = group_by_table(changes)
    assert set(result.keys()) == {"users", "orders"}


def test_group_by_table_invalid_input():
    with pytest.raises(GrouperError):
        group_by_table("not a list")  # type: ignore[arg-type]


def test_group_by_severity_all_breaking():
    changes = [_make(ChangeType.TABLE_REMOVED), _make(ChangeType.COLUMN_REMOVED)]
    result = group_by_severity(changes)
    assert len(result["breaking"]) == 2
    assert len(result["non_breaking"]) == 0


def test_group_by_severity_mixed():
    changes = [
        _make(ChangeType.TABLE_REMOVED),
        _make(ChangeType.TABLE_ADDED),
    ]
    result = group_by_severity(changes)
    assert len(result["breaking"]) == 1
    assert len(result["non_breaking"]) == 1


def test_group_by_severity_invalid_input():
    with pytest.raises(GrouperError):
        group_by_severity(None)  # type: ignore[arg-type]


def test_group_by_change_type_single_type():
    changes = [_make(ChangeType.COLUMN_REMOVED), _make(ChangeType.COLUMN_REMOVED)]
    result = group_by_change_type(changes)
    assert "COLUMN_REMOVED" in result
    assert len(result["COLUMN_REMOVED"]) == 2


def test_group_by_change_type_multiple_types():
    changes = [
        _make(ChangeType.COLUMN_REMOVED),
        _make(ChangeType.TABLE_ADDED),
        _make(ChangeType.INDEX_REMOVED),
    ]
    result = group_by_change_type(changes)
    assert set(result.keys()) == {"COLUMN_REMOVED", "TABLE_ADDED", "INDEX_REMOVED"}


def test_group_by_change_type_invalid_input():
    with pytest.raises(GrouperError):
        group_by_change_type(42)  # type: ignore[arg-type]


def test_group_summary_structure():
    changes = [
        _make(ChangeType.COLUMN_REMOVED, table="users"),
        _make(ChangeType.TABLE_ADDED, table="logs"),
    ]
    summary = group_summary(changes)
    assert "by_table" in summary
    assert "by_severity" in summary
    assert "by_change_type" in summary
    assert summary["by_severity"]["breaking"] == 1
    assert summary["by_severity"]["non_breaking"] == 1


def test_group_summary_empty():
    summary = group_summary([])
    assert summary["by_table"] == {}
    assert summary["by_severity"] == {"breaking": 0, "non_breaking": 0}
    assert summary["by_change_type"] == {}
