"""Tests for schemashift.validator."""

import pytest

from schemashift.comparator import ChangeType, SchemaChange
from schemashift.validator import ValidationResult, ValidatorError, validate


def _make(change_type: ChangeType, table: str = "users", column: str = None) -> SchemaChange:
    return SchemaChange(
        change_type=change_type,
        table=table,
        column=column,
        detail="test detail",
    )


# --- validate returns ValidationResult ---

def test_validate_empty_list_passes():
    result = validate([])
    assert isinstance(result, ValidationResult)
    assert result.passed is True
    assert result.violations == []
    assert result.change_count == 0
    assert result.breaking_count == 0


def test_validate_non_breaking_change_passes():
    changes = [_make(ChangeType.COLUMN_ADDED)]
    result = validate(changes)
    assert result.passed is True
    assert result.breaking_count == 0
    assert result.change_count == 1


def test_validate_breaking_change_counted():
    changes = [_make(ChangeType.TABLE_REMOVED)]
    result = validate(changes)
    assert result.breaking_count == 1
    assert result.passed is True  # no rule set yet


# --- max_breaking rule ---

def test_validate_max_breaking_not_exceeded():
    changes = [_make(ChangeType.TABLE_REMOVED)]
    result = validate(changes, max_breaking=1)
    assert result.passed is True
    assert result.violations == []


def test_validate_max_breaking_exceeded():
    changes = [_make(ChangeType.TABLE_REMOVED), _make(ChangeType.COLUMN_REMOVED, column="email")]
    result = validate(changes, max_breaking=1)
    assert result.passed is False
    assert any("Breaking changes" in v for v in result.violations)


def test_validate_max_breaking_invalid_raises():
    with pytest.raises(ValidatorError):
        validate([], max_breaking=-1)


# --- max_total rule ---

def test_validate_max_total_not_exceeded():
    changes = [_make(ChangeType.COLUMN_ADDED)]
    result = validate(changes, max_total=5)
    assert result.passed is True


def test_validate_max_total_exceeded():
    changes = [_make(ChangeType.COLUMN_ADDED)] * 6
    result = validate(changes, max_total=5)
    assert result.passed is False
    assert any("Total changes" in v for v in result.violations)


def test_validate_max_total_invalid_raises():
    with pytest.raises(ValidatorError):
        validate([], max_total="five")  # type: ignore


# --- allow_table_removal rule ---

def test_validate_table_removal_disallowed():
    changes = [_make(ChangeType.TABLE_REMOVED, table="orders")]
    result = validate(changes, allow_table_removal=False)
    assert result.passed is False
    assert any("orders" in v for v in result.violations)


def test_validate_table_removal_allowed_by_default():
    changes = [_make(ChangeType.TABLE_REMOVED)]
    result = validate(changes)
    assert result.passed is True


# --- allow_column_removal rule ---

def test_validate_column_removal_disallowed():
    changes = [_make(ChangeType.COLUMN_REMOVED, table="users", column="phone")]
    result = validate(changes, allow_column_removal=False)
    assert result.passed is False
    assert any("users.phone" in v for v in result.violations)


# --- as_dict ---

def test_validation_result_as_dict():
    result = ValidationResult(passed=False, violations=["too many"], change_count=3, breaking_count=2)
    d = result.as_dict()
    assert d["passed"] is False
    assert d["violations"] == ["too many"]
    assert d["change_count"] == 3
    assert d["breaking_count"] == 2


# --- invalid input ---

def test_validate_non_list_raises():
    with pytest.raises(ValidatorError):
        validate("not a list")  # type: ignore
