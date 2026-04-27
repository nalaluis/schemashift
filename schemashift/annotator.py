"""Annotate schema changes with human-readable migration hints."""

from typing import List, Dict
from schemashift.comparator import SchemaChange, ChangeType


class AnnotatorError(Exception):
    """Raised when annotation fails."""


_HINTS: Dict[ChangeType, str] = {
    ChangeType.TABLE_REMOVED: (
        "Ensure all application references to this table are removed "
        "before dropping it in production."
    ),
    ChangeType.TABLE_ADDED: (
        "New table detected. Verify default values and NOT NULL constraints "
        "are compatible with existing application code."
    ),
    ChangeType.COLUMN_REMOVED: (
        "Removing a column is irreversible. Back up data and update all "
        "queries that reference this column."
    ),
    ChangeType.COLUMN_ADDED: (
        "Adding a column is generally safe. If NOT NULL without a default, "
        "existing rows may fail insertion checks."
    ),
    ChangeType.COLUMN_TYPE_CHANGED: (
        "Type changes may cause implicit cast failures or data truncation. "
        "Test with production-like data volumes before deploying."
    ),
    ChangeType.INDEX_REMOVED: (
        "Removing an index can degrade query performance. Review slow-query "
        "logs after deployment."
    ),
    ChangeType.INDEX_ADDED: (
        "New index will be built on existing rows. This may lock the table "
        "on older database versions."
    ),
}

_DEFAULT_HINT = "Review this change carefully before applying to production."


def annotate(change: SchemaChange) -> str:
    """Return a migration hint string for a single SchemaChange."""
    if not isinstance(change, SchemaChange):
        raise AnnotatorError(f"Expected SchemaChange, got {type(change).__name__}")
    return _HINTS.get(change.change_type, _DEFAULT_HINT)


def annotate_all(changes: List[SchemaChange]) -> List[Dict]:
    """Return a list of dicts pairing each change with its annotation."""
    if not isinstance(changes, list):
        raise AnnotatorError("changes must be a list")
    return [
        {
            "change": str(change),
            "change_type": change.change_type.value,
            "breaking": change.breaking,
            "hint": annotate(change),
        }
        for change in changes
    ]
