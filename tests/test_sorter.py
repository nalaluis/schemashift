"""Tests for schemashift.sorter."""

import pytest
from schemashift.comparator import SchemaChange, ChangeType
from schemashift.sorter import (
    SorterError,
    sort_by_severity,
    sort_by_change_type,
    sort_by_table,
    sort_changes,
)


def _make(change_type: ChangeType, table: str = "users") -> SchemaChange:
    return SchemaChange(
        change_type=change_type,
        table=table,
        description=f"{change_type.value} on {table}",
    )


def test_sort_by_severity_breaking_first():
    changes = [
        _make(ChangeType.COLUMN_ADDED),
        _make(ChangeType.TABLE_REMOVED),
        _make(ChangeType.COLUMN_REMOVED),
    ]
    result = sort_by_severity(changes)
    assert result[0].change_type == ChangeType.TABLE_REMOVED
    assert result[1].change_type == ChangeType.COLUMN_REMOVED
    assert result[2].change_type == ChangeType.COLUMN_ADDED


def test_sort_by_severity_empty():
    assert sort_by_severity([]) == []


def test_sort_by_severity_invalid_input():
    with pytest.raises(SorterError):
        sort_by_severity("not a list")  # type: ignore


def test_sort_by_change_type_order():
    changes = [
        _make(ChangeType.COLUMN_ADDED),
        _make(ChangeType.INDEX_REMOVED),
        _make(ChangeType.TABLE_REMOVED),
    ]
    result = sort_by_change_type(changes)
    assert result[0].change_type == ChangeType.TABLE_REMOVED
    assert result[1].change_type == ChangeType.INDEX_REMOVED
    assert result[2].change_type == ChangeType.COLUMN_ADDED


def test_sort_by_change_type_empty():
    assert sort_by_change_type([]) == []


def test_sort_by_change_type_invalid_input():
    with pytest.raises(SorterError):
        sort_by_change_type(None)  # type: ignore


def test_sort_by_table_alphabetical():
    changes = [
        _make(ChangeType.COLUMN_REMOVED, table="orders"),
        _make(ChangeType.COLUMN_REMOVED, table="accounts"),
        _make(ChangeType.COLUMN_REMOVED, table="users"),
    ]
    result = sort_by_table(changes)
    assert [c.table for c in result] == ["accounts", "orders", "users"]


def test_sort_by_table_reverse():
    changes = [
        _make(ChangeType.COLUMN_REMOVED, table="accounts"),
        _make(ChangeType.COLUMN_REMOVED, table="users"),
    ]
    result = sort_by_table(changes, reverse=True)
    assert result[0].table == "users"
    assert result[1].table == "accounts"


def test_sort_by_table_invalid_input():
    with pytest.raises(SorterError):
        sort_by_table(42)  # type: ignore


def test_sort_changes_primary_severity():
    changes = [
        _make(ChangeType.TABLE_ADDED),
        _make(ChangeType.TABLE_REMOVED),
    ]
    result = sort_changes(changes, primary="severity")
    assert result[0].change_type == ChangeType.TABLE_REMOVED


def test_sort_changes_primary_table():
    changes = [
        _make(ChangeType.COLUMN_REMOVED, table="zebra"),
        _make(ChangeType.COLUMN_REMOVED, table="alpha"),
    ]
    result = sort_changes(changes, primary="table")
    assert result[0].table == "alpha"


def test_sort_changes_invalid_primary():
    with pytest.raises(SorterError, match="Unknown sort key"):
        sort_changes([], primary="nonexistent")


def test_sort_changes_invalid_secondary():
    with pytest.raises(SorterError, match="Unknown secondary sort key"):
        sort_changes([], primary="severity", secondary="bogus")


def test_sort_changes_with_secondary():
    changes = [
        _make(ChangeType.TABLE_ADDED, table="zebra"),
        _make(ChangeType.TABLE_REMOVED, table="alpha"),
        _make(ChangeType.COLUMN_REMOVED, table="beta"),
    ]
    result = sort_changes(changes, primary="severity", secondary="table")
    # Breaking changes first, then sorted by table within groups
    assert result[0].change_type in (ChangeType.TABLE_REMOVED, ChangeType.COLUMN_REMOVED)
