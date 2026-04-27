"""Tests for schemashift.summarizer."""

import pytest

from schemashift.comparator import ChangeType, SchemaChange
from schemashift.summarizer import DiffSummary, SummarizerError, format_summary, summarize


def _make(change_type: ChangeType, table: str = "users", column: str = None) -> SchemaChange:
    return SchemaChange(
        change_type=change_type,
        table=table,
        column=column,
        detail="test detail",
    )


def test_summarize_empty_list():
    summary = summarize([])
    assert summary.total == 0
    assert summary.breaking == 0
    assert summary.non_breaking == 0
    assert summary.tables_affected == 0
    assert summary.change_type_counts == {}


def test_summarize_counts_breaking():
    changes = [
        _make(ChangeType.TABLE_REMOVED),
        _make(ChangeType.COLUMN_REMOVED, column="email"),
        _make(ChangeType.TABLE_ADDED, table="orders"),
    ]
    summary = summarize(changes)
    assert summary.total == 3
    assert summary.breaking == 2
    assert summary.non_breaking == 1


def test_summarize_tables_affected():
    changes = [
        _make(ChangeType.COLUMN_REMOVED, table="users", column="email"),
        _make(ChangeType.COLUMN_REMOVED, table="users", column="name"),
        _make(ChangeType.TABLE_REMOVED, table="orders"),
    ]
    summary = summarize(changes)
    assert summary.tables_affected == 2


def test_summarize_change_type_counts():
    changes = [
        _make(ChangeType.TABLE_REMOVED),
        _make(ChangeType.TABLE_REMOVED, table="posts"),
        _make(ChangeType.COLUMN_ADDED, column="bio"),
    ]
    summary = summarize(changes)
    assert summary.change_type_counts[ChangeType.TABLE_REMOVED.value] == 2
    assert summary.change_type_counts[ChangeType.COLUMN_ADDED.value] == 1


def test_summarize_invalid_input_raises():
    with pytest.raises(SummarizerError):
        summarize("not a list")


def test_as_dict_structure():
    summary = summarize([_make(ChangeType.TABLE_ADDED, table="logs")])
    d = summary.as_dict()
    assert set(d.keys()) == {"total", "breaking", "non_breaking", "tables_affected", "change_type_counts"}


def test_format_summary_contains_key_fields():
    changes = [
        _make(ChangeType.COLUMN_REMOVED, column="id"),
        _make(ChangeType.TABLE_ADDED, table="metrics"),
    ]
    summary = summarize(changes)
    text = format_summary(summary)
    assert "Total changes" in text
    assert "Breaking" in text
    assert "Non-breaking" in text
    assert "Tables affected" in text


def test_format_summary_no_changes():
    summary = summarize([])
    text = format_summary(summary)
    assert "0" in text
    assert "Schema Diff Summary" in text
