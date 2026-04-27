"""Tests for schemashift.filter."""

import pytest
from schemashift.comparator import SchemaChange, ChangeType
from schemashift.filter import filter_changes, partition_by_severity, FilterError


def _make(change_type: ChangeType, table: str = "users") -> SchemaChange:
    return SchemaChange(change_type=change_type, table=table, description="test change")


BREAKING = [
    _make(ChangeType.TABLE_REMOVED, "orders"),
    _make(ChangeType.COLUMN_REMOVED, "users"),
    _make(ChangeType.COLUMN_TYPE_CHANGED, "users"),
]

NON_BREAKING = [
    _make(ChangeType.TABLE_ADDED, "logs"),
    _make(ChangeType.COLUMN_ADDED, "users"),
]

ALL_CHANGES = BREAKING + NON_BREAKING


def test_filter_no_filters_returns_all():
    assert filter_changes(ALL_CHANGES) == ALL_CHANGES


def test_filter_severity_breaking():
    result = filter_changes(ALL_CHANGES, severity="breaking")
    assert len(result) == len(BREAKING)
    assert all(c in BREAKING for c in result)


def test_filter_severity_non_breaking():
    result = filter_changes(ALL_CHANGES, severity="non-breaking")
    assert len(result) == len(NON_BREAKING)
    assert all(c in NON_BREAKING for c in result)


def test_filter_invalid_severity_raises():
    with pytest.raises(FilterError, match="Invalid severity"):
        filter_changes(ALL_CHANGES, severity="critical")


def test_filter_by_change_type():
    result = filter_changes(ALL_CHANGES, change_types=["COLUMN_REMOVED"])
    assert all(c.change_type == ChangeType.COLUMN_REMOVED for c in result)
    assert len(result) == 1


def test_filter_by_multiple_change_types():
    result = filter_changes(ALL_CHANGES, change_types=["TABLE_ADDED", "COLUMN_ADDED"])
    assert len(result) == 2


def test_filter_unknown_change_type_raises():
    with pytest.raises(FilterError, match="Unknown change type"):
        filter_changes(ALL_CHANGES, change_types=["NONEXISTENT_TYPE"])


def test_filter_by_table():
    result = filter_changes(ALL_CHANGES, tables=["users"])
    assert all(c.table == "users" for c in result)


def test_filter_by_table_no_match():
    result = filter_changes(ALL_CHANGES, tables=["nonexistent"])
    assert result == []


def test_filter_combined_severity_and_table():
    result = filter_changes(ALL_CHANGES, severity="breaking", tables=["users"])
    assert all(c.table == "users" for c in result)
    assert len(result) == 2  # COLUMN_REMOVED + COLUMN_TYPE_CHANGED on users


def test_partition_by_severity_counts():
    parts = partition_by_severity(ALL_CHANGES)
    assert len(parts["breaking"]) == len(BREAKING)
    assert len(parts["non_breaking"]) == len(NON_BREAKING)


def test_partition_by_severity_empty():
    parts = partition_by_severity([])
    assert parts["breaking"] == []
    assert parts["non_breaking"] == []


def test_filter_empty_changes():
    assert filter_changes([], severity="breaking") == []
