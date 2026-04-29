"""Validates a list of SchemaChange objects against configurable rules."""

from dataclasses import dataclass, field
from typing import List, Optional

from schemashift.comparator import SchemaChange
from schemashift.differ import is_breaking


class ValidatorError(Exception):
    """Raised when validation configuration is invalid."""


@dataclass
class ValidationResult:
    passed: bool
    violations: List[str] = field(default_factory=list)
    change_count: int = 0
    breaking_count: int = 0

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "violations": self.violations,
            "change_count": self.change_count,
            "breaking_count": self.breaking_count,
        }


def validate(
    changes: List[SchemaChange],
    *,
    max_breaking: Optional[int] = None,
    max_total: Optional[int] = None,
    allow_table_removal: bool = True,
    allow_column_removal: bool = True,
) -> ValidationResult:
    """Validate a list of schema changes against the supplied rules.

    Args:
        changes: List of SchemaChange objects to validate.
        max_breaking: If set, fail when breaking changes exceed this count.
        max_total: If set, fail when total changes exceed this count.
        allow_table_removal: When False, any TABLE_REMOVED change is a violation.
        allow_column_removal: When False, any COLUMN_REMOVED change is a violation.

    Returns:
        A ValidationResult describing whether the diff is acceptable.
    """
    if not isinstance(changes, list):
        raise ValidatorError("changes must be a list of SchemaChange objects")

    violations: List[str] = []
    breaking_count = sum(1 for c in changes if is_breaking(c))
    total_count = len(changes)

    if max_breaking is not None:
        if not isinstance(max_breaking, int) or max_breaking < 0:
            raise ValidatorError("max_breaking must be a non-negative integer")
        if breaking_count > max_breaking:
            violations.append(
                f"Breaking changes ({breaking_count}) exceed allowed maximum ({max_breaking})"
            )

    if max_total is not None:
        if not isinstance(max_total, int) or max_total < 0:
            raise ValidatorError("max_total must be a non-negative integer")
        if total_count > max_total:
            violations.append(
                f"Total changes ({total_count}) exceed allowed maximum ({max_total})"
            )

    for change in changes:
        if not allow_table_removal and change.change_type.name == "TABLE_REMOVED":
            violations.append(
                f"Table removal is not allowed: '{change.table}'"
            )
        if not allow_column_removal and change.change_type.name == "COLUMN_REMOVED":
            col = change.column or "unknown"
            violations.append(
                f"Column removal is not allowed: '{change.table}.{col}'"
            )

    return ValidationResult(
        passed=len(violations) == 0,
        violations=violations,
        change_count=total_count,
        breaking_count=breaking_count,
    )
