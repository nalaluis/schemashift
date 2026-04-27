"""Tests for schemashift.annotator."""

import pytest
from schemashift.comparator import SchemaChange, ChangeType
from schemashift.annotator import annotate, annotate_all, AnnotatorError, _DEFAULT_HINT


def _make(change_type: ChangeType, breaking: bool = True) -> SchemaChange:
    return SchemaChange(
        change_type=change_type,
        description=f"test change {change_type.value}",
        table="users",
        breaking=breaking,
    )


def test_annotate_returns_string_for_known_type():
    change = _make(ChangeType.TABLE_REMOVED)
    hint = annotate(change)
    assert isinstance(hint, str)
    assert len(hint) > 0


def test_annotate_table_removed_mentions_drop():
    hint = annotate(_make(ChangeType.TABLE_REMOVED))
    assert "drop" in hint.lower() or "dropping" in hint.lower() or "production" in hint.lower()


def test_annotate_column_type_changed_mentions_cast():
    hint = annotate(_make(ChangeType.COLUMN_TYPE_CHANGED))
    assert "cast" in hint.lower() or "type" in hint.lower()


def test_annotate_index_removed_mentions_performance():
    hint = annotate(_make(ChangeType.INDEX_REMOVED))
    assert "performance" in hint.lower() or "query" in hint.lower()


def test_annotate_raises_for_non_change():
    with pytest.raises(AnnotatorError):
        annotate("not a change")  # type: ignore[arg-type]


def test_annotate_all_returns_list_of_dicts():
    changes = [_make(ChangeType.COLUMN_REMOVED), _make(ChangeType.TABLE_ADDED, breaking=False)]
    result = annotate_all(changes)
    assert len(result) == 2
    for entry in result:
        assert "change" in entry
        assert "hint" in entry
        assert "breaking" in entry
        assert "change_type" in entry


def test_annotate_all_empty_list():
    assert annotate_all([]) == []


def test_annotate_all_raises_for_non_list():
    with pytest.raises(AnnotatorError):
        annotate_all("not a list")  # type: ignore[arg-type]


def test_annotate_all_breaking_flag_preserved():
    changes = [
        _make(ChangeType.COLUMN_REMOVED, breaking=True),
        _make(ChangeType.COLUMN_ADDED, breaking=False),
    ]
    result = annotate_all(changes)
    assert result[0]["breaking"] is True
    assert result[1]["breaking"] is False


def test_annotate_all_change_type_value_is_string():
    result = annotate_all([_make(ChangeType.INDEX_ADDED)])
    assert isinstance(result[0]["change_type"], str)
