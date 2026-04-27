"""Tests for schemashift.scorer."""

import pytest

from schemashift.comparator import SchemaChange, ChangeType
from schemashift.scorer import score_diff, DiffScore, ScorerError


def _make(change_type: ChangeType, table: str = "users", detail: str = "") -> SchemaChange:
    return SchemaChange(change_type=change_type, table=table, detail=detail)


def test_score_empty_list():
    result = score_diff([])
    assert isinstance(result, DiffScore)
    assert result.total == 0
    assert result.risk_level == "low"
    assert result.breakdown == {}


def test_score_single_table_removed():
    result = score_diff([_make(ChangeType.TABLE_REMOVED)])
    assert result.total == 10
    assert result.risk_level == "medium"


def test_score_single_column_added_is_low():
    result = score_diff([_make(ChangeType.COLUMN_ADDED)])
    assert result.total == 1
    assert result.risk_level == "low"


def test_score_accumulates_multiple_changes():
    changes = [
        _make(ChangeType.TABLE_REMOVED),
        _make(ChangeType.COLUMN_REMOVED, table="orders"),
        _make(ChangeType.COLUMN_REMOVED, table="products"),
    ]
    result = score_diff(changes)
    # 10 + 8 + 8 = 26
    assert result.total == 26
    assert result.risk_level == "high"


def test_score_critical_threshold():
    changes = [_make(ChangeType.TABLE_REMOVED)] * 4  # 4 * 10 = 40
    result = score_diff(changes)
    assert result.total == 40
    assert result.risk_level == "critical"


def test_breakdown_contains_count_weight_subtotal():
    changes = [
        _make(ChangeType.COLUMN_TYPE_CHANGED),
        _make(ChangeType.COLUMN_TYPE_CHANGED),
    ]
    result = score_diff(changes)
    ct = ChangeType.COLUMN_TYPE_CHANGED
    assert ct in result.breakdown
    count, weight, subtotal = result.breakdown[ct]
    assert count == 2
    assert weight == 7
    assert subtotal == 14


def test_as_dict_structure():
    changes = [_make(ChangeType.INDEX_REMOVED)]
    result = score_diff(changes).as_dict()
    assert "total" in result
    assert "risk_level" in result
    assert "breakdown" in result
    key = ChangeType.INDEX_REMOVED.value
    assert key in result["breakdown"]
    entry = result["breakdown"][key]
    assert entry["count"] == 1
    assert entry["weight"] == 4
    assert entry["subtotal"] == 4


def test_score_diff_raises_on_non_list():
    with pytest.raises(ScorerError):
        score_diff("not a list")


def test_mixed_breaking_and_non_breaking():
    changes = [
        _make(ChangeType.TABLE_ADDED),
        _make(ChangeType.COLUMN_ADDED),
        _make(ChangeType.COLUMN_REMOVED),
    ]
    result = score_diff(changes)
    # 1 + 1 + 8 = 10
    assert result.total == 10
    assert result.risk_level == "medium"
