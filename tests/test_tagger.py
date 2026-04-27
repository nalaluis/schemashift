"""Tests for schemashift.tagger."""

import pytest
from schemashift.comparator import SchemaChange, ChangeType
from schemashift.tagger import (
    TaggerError,
    tag_change,
    tag_all,
    filter_by_tag,
)


def _make(change_type: ChangeType, table: str = "users", detail: str = "") -> SchemaChange:
    return SchemaChange(change_type=change_type, table=table, description=detail or str(change_type))


# ---------------------------------------------------------------------------
# tag_change
# ---------------------------------------------------------------------------

def test_tag_change_table_removed_includes_destructive():
    change = _make(ChangeType.TABLE_REMOVED)
    tags = tag_change(change)
    assert "destructive" in tags
    assert "data-loss" in tags


def test_tag_change_column_added_is_additive():
    change = _make(ChangeType.COLUMN_ADDED)
    tags = tag_change(change)
    assert "additive" in tags
    assert "destructive" not in tags


def test_tag_change_extra_tags_are_appended():
    change = _make(ChangeType.TABLE_ADDED)
    tags = tag_change(change, extra_tags=["reviewed", "sprint-42"])
    assert "reviewed" in tags
    assert "sprint-42" in tags


def test_tag_change_no_duplicate_extra_tags():
    change = _make(ChangeType.TABLE_ADDED)
    tags = tag_change(change, extra_tags=["additive"])  # already present
    assert tags.count("additive") == 1


def test_tag_change_invalid_input_raises():
    with pytest.raises(TaggerError):
        tag_change("not-a-change")  # type: ignore[arg-type]


def test_tag_change_non_string_extra_tag_raises():
    change = _make(ChangeType.COLUMN_REMOVED)
    with pytest.raises(TaggerError):
        tag_change(change, extra_tags=[123])  # type: ignore[list-item]


# ---------------------------------------------------------------------------
# tag_all
# ---------------------------------------------------------------------------

def test_tag_all_returns_dict_keyed_by_description():
    changes = [_make(ChangeType.TABLE_REMOVED), _make(ChangeType.COLUMN_ADDED, table="orders")]
    result = tag_all(changes)
    assert isinstance(result, dict)
    assert len(result) == 2


def test_tag_all_empty_list_returns_empty_dict():
    assert tag_all([]) == {}


def test_tag_all_invalid_input_raises():
    with pytest.raises(TaggerError):
        tag_all("not-a-list")  # type: ignore[arg-type]


def test_tag_all_propagates_extra_tags():
    changes = [_make(ChangeType.INDEX_REMOVED)]
    result = tag_all(changes, extra_tags=["needs-review"])
    tags = list(result.values())[0]
    assert "needs-review" in tags


# ---------------------------------------------------------------------------
# filter_by_tag
# ---------------------------------------------------------------------------

def test_filter_by_tag_keeps_matching_changes():
    changes = [
        _make(ChangeType.TABLE_REMOVED),
        _make(ChangeType.TABLE_ADDED),
    ]
    result = filter_by_tag(changes, "destructive")
    assert len(result) == 1
    assert result[0].change_type == ChangeType.TABLE_REMOVED


def test_filter_by_tag_returns_empty_when_no_match():
    changes = [_make(ChangeType.COLUMN_ADDED)]
    result = filter_by_tag(changes, "destructive")
    assert result == []


def test_filter_by_tag_invalid_tag_raises():
    with pytest.raises(TaggerError):
        filter_by_tag([], "")  # empty string


def test_filter_by_tag_non_string_raises():
    with pytest.raises(TaggerError):
        filter_by_tag([], 42)  # type: ignore[arg-type]
