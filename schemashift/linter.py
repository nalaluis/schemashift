"""Lint schema changes and emit structured warnings or errors."""

from dataclasses import dataclass, field
from typing import List, Optional
from schemashift.comparator import SchemaChange, ChangeType
from schemashift.differ import is_breaking


class LinterError(Exception):
    """Raised when linting cannot be performed."""


@dataclass
class LintIssue:
    change: SchemaChange
    level: str          # "error" | "warning"
    rule: str
    message: str

    def as_dict(self) -> dict:
        return {
            "level": self.level,
            "rule": self.rule,
            "table": self.change.table,
            "change_type": self.change.change_type.value,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Built-in rules
# ---------------------------------------------------------------------------

def _rule_breaking_must_have_description(change: SchemaChange) -> Optional[LintIssue]:
    """Breaking changes should carry a non-empty description."""
    if is_breaking(change) and not change.description.strip():
        return LintIssue(
            change=change,
            level="warning",
            rule="breaking-needs-description",
            message=(
                f"{change.change_type.value} on '{change.table}' is breaking "
                "but has no description."
            ),
        )
    return None


def _rule_no_bare_type_change(change: SchemaChange) -> Optional[LintIssue]:
    """Column type changes must name both old and new types in the description."""
    if change.change_type == ChangeType.COLUMN_TYPE_CHANGED:
        desc = change.description
        if "->" not in desc and "to" not in desc.lower():
            return LintIssue(
                change=change,
                level="error",
                rule="type-change-must-document-types",
                message=(
                    f"Column type change on '{change.table}' should document "
                    "old and new types (e.g. 'int -> bigint')."
                ),
            )
    return None


_DEFAULT_RULES = [
    _rule_breaking_must_have_description,
    _rule_no_bare_type_change,
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def lint(changes: List[SchemaChange]) -> List[LintIssue]:
    """Run all built-in lint rules against *changes* and return issues."""
    if not isinstance(changes, list):
        raise LinterError("changes must be a list of SchemaChange objects")
    issues: List[LintIssue] = []
    for change in changes:
        for rule_fn in _DEFAULT_RULES:
            issue = rule_fn(change)
            if issue is not None:
                issues.append(issue)
    return issues


def has_errors(issues: List[LintIssue]) -> bool:
    """Return True if any issue has level 'error'."""
    return any(i.level == "error" for i in issues)
