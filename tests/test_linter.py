"""Tests for schemashift.linter."""

import pytest
from schemashift.comparator import SchemaChange, ChangeType
from schemashift.linter import (
    LinterError,
    LintIssue,
    lint,
    has_errors,
)


def _make(
    change_type: ChangeType,
    table: str = "users",
    description: str = "",
) -> SchemaChange:
    return SchemaChange(change_type=change_type, table=table, description=description)


# ---------------------------------------------------------------------------
# lint()
# ---------------------------------------------------------------------------

def test_lint_empty_list_returns_no_issues():
    assert lint([]) == []


def test_lint_invalid_input_raises():
    with pytest.raises(LinterError):
        lint("not a list")  # type: ignore


def test_lint_non_breaking_no_description_no_issue():
    change = _make(ChangeType.COLUMN_ADDED, description="")
    issues = lint([change])
    # COLUMN_ADDED is not breaking, so breaking-needs-description should not fire
    rules_fired = {i.rule for i in issues}
    assert "breaking-needs-description" not in rules_fired


def test_lint_breaking_without_description_emits_warning():
    change = _make(ChangeType.TABLE_REMOVED, description="")
    issues = lint([change])
    rules = [i.rule for i in issues]
    assert "breaking-needs-description" in rules


def test_lint_breaking_with_description_no_warning():
    change = _make(ChangeType.TABLE_REMOVED, description="Deprecated table dropped")
    issues = lint([change])
    rules = [i.rule for i in issues]
    assert "breaking-needs-description" not in rules


def test_lint_type_change_without_types_emits_error():
    change = _make(ChangeType.COLUMN_TYPE_CHANGED, description="changed column")
    issues = lint([change])
    rules = [i.rule for i in issues]
    assert "type-change-must-document-types" in rules
    levels = [i.level for i in issues if i.rule == "type-change-must-document-types"]
    assert levels == ["error"]


def test_lint_type_change_with_arrow_notation_no_error():
    change = _make(ChangeType.COLUMN_TYPE_CHANGED, description="int -> bigint")
    issues = lint([change])
    rules = [i.rule for i in issues]
    assert "type-change-must-document-types" not in rules


def test_lint_type_change_with_to_keyword_no_error():
    change = _make(ChangeType.COLUMN_TYPE_CHANGED, description="changed from varchar to text")
    issues = lint([change])
    rules = [i.rule for i in issues]
    assert "type-change-must-document-types" not in rules


def test_lint_issue_as_dict_contains_expected_keys():
    change = _make(ChangeType.TABLE_REMOVED, description="")
    issues = lint([change])
    assert issues
    d = issues[0].as_dict()
    for key in ("level", "rule", "table", "change_type", "message"):
        assert key in d


# ---------------------------------------------------------------------------
# has_errors()
# ---------------------------------------------------------------------------

def test_has_errors_false_when_only_warnings():
    change = _make(ChangeType.TABLE_REMOVED, description="")
    issues = lint([change])
    # breaking-needs-description fires as warning; no errors expected here
    assert not has_errors(issues)


def test_has_errors_true_when_error_present():
    change = _make(ChangeType.COLUMN_TYPE_CHANGED, description="changed")
    issues = lint([change])
    assert has_errors(issues)


def test_has_errors_false_for_empty_list():
    assert not has_errors([])
