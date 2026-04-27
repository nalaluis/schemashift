"""Scores schema diffs by assigning a numeric risk level based on change composition."""

from dataclasses import dataclass
from typing import List

from schemashift.comparator import SchemaChange, ChangeType


class ScorerError(Exception):
    """Raised when scoring fails due to invalid input."""


# Risk weights per change type (higher = riskier)
_WEIGHTS: dict[ChangeType, int] = {
    ChangeType.TABLE_REMOVED: 10,
    ChangeType.COLUMN_REMOVED: 8,
    ChangeType.COLUMN_TYPE_CHANGED: 7,
    ChangeType.INDEX_REMOVED: 4,
    ChangeType.CONSTRAINT_REMOVED: 5,
    ChangeType.TABLE_ADDED: 1,
    ChangeType.COLUMN_ADDED: 1,
    ChangeType.INDEX_ADDED: 1,
    ChangeType.CONSTRAINT_ADDED: 1,
}

_THRESHOLDS = {
    "low": 5,
    "medium": 15,
    "high": 30,
}


@dataclass
class DiffScore:
    total: int
    risk_level: str  # "low", "medium", "high", "critical"
    breakdown: dict  # ChangeType -> (count, weight, subtotal)

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "risk_level": self.risk_level,
            "breakdown": {
                ct.value: {"count": v[0], "weight": v[1], "subtotal": v[2]}
                for ct, v in self.breakdown.items()
            },
        }


def _risk_level(score: int) -> str:
    if score <= _THRESHOLDS["low"]:
        return "low"
    if score <= _THRESHOLDS["medium"]:
        return "medium"
    if score <= _THRESHOLDS["high"]:
        return "high"
    return "critical"


def score_diff(changes: List[SchemaChange]) -> DiffScore:
    """Compute a numeric risk score for a list of schema changes.

    Args:
        changes: List of SchemaChange objects produced by compare_schemas.

    Returns:
        A DiffScore with total score, risk level, and per-type breakdown.

    Raises:
        ScorerError: If changes is not a list.
    """
    if not isinstance(changes, list):
        raise ScorerError("changes must be a list of SchemaChange objects")

    counts: dict[ChangeType, int] = {}
    for change in changes:
        counts[change.change_type] = counts.get(change.change_type, 0) + 1

    breakdown = {}
    total = 0
    for ct, count in counts.items():
        weight = _WEIGHTS.get(ct, 2)
        subtotal = count * weight
        breakdown[ct] = (count, weight, subtotal)
        total += subtotal

    return DiffScore(total=total, risk_level=_risk_level(total), breakdown=breakdown)
