"""Tests for schemashift.merger."""

import pytest
from schemashift.comparator import SchemaChange, ChangeType
from schemashift.merger import merge_diffs, merge_by_table, count_by_source, MergerError


def _make(change_type, table="users", column=None, breaking=True, detail=""):
    return SchemaChange(
        change_type=change_type,
        table=table,
        column=column,
        breaking=breaking,
        detail=detail,
    )


def test_merge_diffs_empty_lists():
    result = merge_diffs([], [])
    assert result == []


def test_merge_diffs_single_list():
    changes = [_make(ChangeType.COLUMN_REMOVED, column="email")]
    result = merge_diffs(changes)
    assert len(result) == 1
    assert result[0].column == "email"


def test_merge_diffs_combines_two_lists():
    diff1 = [_make(ChangeType.TABLE_REMOVED, table="orders")]
    diff2 = [_make(ChangeType.COLUMN_REMOVED, table="users", column="name")]
    result = merge_diffs(diff1, diff2)
    assert len(result) == 2


def test_merge_diffs_deduplicates():
    change = _make(ChangeType.COLUMN_REMOVED, column="email")
    result = merge_diffs([change], [change])
    assert len(result) == 1


def test_merge_diffs_invalid_input_raises():
    with pytest.raises(MergerError, match="not a list"):
        merge_diffs("not a list")


def test_merge_diffs_invalid_item_raises():
    with pytest.raises(MergerError, match="not a SchemaChange"):
        merge_diffs(["bad_item"])


def test_merge_by_table_groups_correctly():
    diff1 = [_make(ChangeType.COLUMN_REMOVED, table="users", column="email")]
    diff2 = [_make(ChangeType.TABLE_REMOVED, table="orders")]
    result = merge_by_table(diff1, diff2)
    assert "users" in result
    assert "orders" in result
    assert len(result["users"]) == 1


def test_merge_by_table_empty():
    result = merge_by_table([], [])
    assert result == {}


def test_count_by_source_returns_lengths():
    diff1 = [_make(ChangeType.TABLE_REMOVED, table="a")]
    diff2 = [_make(ChangeType.COLUMN_REMOVED, table="b", column="x"),
             _make(ChangeType.COLUMN_REMOVED, table="b", column="y")]
    counts = count_by_source(diff1, diff2)
    assert counts == [1, 2]


def test_count_by_source_invalid_raises():
    with pytest.raises(MergerError):
        count_by_source(42)


def test_merge_diffs_preserves_change_types():
    diff1 = [_make(ChangeType.TABLE_ADDED, table="new_table", breaking=False)]
    diff2 = [_make(ChangeType.COLUMN_TYPE_CHANGED, table="users", column="age", detail="int->text")]
    result = merge_diffs(diff1, diff2)
    types = {c.change_type for c in result}
    assert ChangeType.TABLE_ADDED in types
    assert ChangeType.COLUMN_TYPE_CHANGED in types
