"""Tests for schemashift.deduplicator."""

import pytest
from schemashift.comparator import ChangeType, SchemaChange
from schemashift.deduplicator import (
    DeduplicatorError,
    deduplicate,
    count_duplicates,
)


def _make(
    change_type=ChangeType.COLUMN_REMOVED,
    table="users",
    column="email",
    old_value="varchar",
    new_value=None,
):
    return SchemaChange(
        change_type=change_type,
        table=table,
        column=column,
        old_value=old_value,
        new_value=new_value,
    )


def test_deduplicate_empty_list():
    assert deduplicate([]) == []


def test_deduplicate_no_duplicates_returns_same_items():
    a = _make(table="users")
    b = _make(table="orders")
    result = deduplicate([a, b])
    assert result == [a, b]


def test_deduplicate_removes_exact_duplicate():
    a = _make()
    b = _make()  # identical fields
    result = deduplicate([a, b])
    assert len(result) == 1
    assert result[0] is a


def test_deduplicate_preserves_first_occurrence_order():
    a = _make(table="alpha")
    b = _make(table="beta")
    c = _make(table="alpha")  # duplicate of a
    result = deduplicate([a, b, c])
    assert [r.table for r in result] == ["alpha", "beta"]


def test_deduplicate_different_change_types_not_deduplicated():
    a = _make(change_type=ChangeType.COLUMN_REMOVED)
    b = _make(change_type=ChangeType.COLUMN_TYPE_CHANGED, new_value="text")
    result = deduplicate([a, b])
    assert len(result) == 2


def test_deduplicate_different_old_values_not_deduplicated():
    a = _make(old_value="int")
    b = _make(old_value="bigint")
    result = deduplicate([a, b])
    assert len(result) == 2


def test_deduplicate_invalid_input_raises():
    with pytest.raises(DeduplicatorError, match="must be a list"):
        deduplicate("not a list")


def test_deduplicate_non_schema_change_item_raises():
    with pytest.raises(DeduplicatorError, match="index 1"):
        deduplicate([_make(), "bad item"])


def test_count_duplicates_no_duplicates():
    changes = [_make(table="a"), _make(table="b")]
    assert count_duplicates(changes) == 0


def test_count_duplicates_with_duplicates():
    a = _make()
    changes = [a, _make(), _make(table="other")]
    # a and _make() share the same key -> 1 duplicate
    assert count_duplicates(changes) == 1


def test_count_duplicates_invalid_input_raises():
    with pytest.raises(DeduplicatorError):
        count_duplicates(None)
