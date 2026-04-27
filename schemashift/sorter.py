"""Sort and prioritize schema changes for reporting and triage."""

from typing import List, Optional
from schemashift.comparator import SchemaChange, ChangeType
from schemashift.differ import is_breaking


class SorterError(Exception):
    """Raised when sorting operations fail."""


# Lower number = higher priority
_CHANGE_TYPE_PRIORITY = {
    ChangeType.TABLE_REMOVED: 1,
    ChangeType.COLUMN_REMOVED: 2,
    ChangeType.COLUMN_TYPE_CHANGED: 3,
    ChangeType.INDEX_REMOVED: 4,
    ChangeType.CONSTRAINT_REMOVED: 5,
    ChangeType.TABLE_ADDED: 6,
    ChangeType.COLUMN_ADDED: 7,
    ChangeType.INDEX_ADDED: 8,
    ChangeType.CONSTRAINT_ADDED: 9,
}

_DEFAULT_PRIORITY = 99


def _change_priority(change: SchemaChange) -> int:
    return _CHANGE_TYPE_PRIORITY.get(change.change_type, _DEFAULT_PRIORITY)


def sort_by_severity(changes: List[SchemaChange]) -> List[SchemaChange]:
    """Sort changes so breaking changes come before non-breaking ones.
    Within each group, preserve original order.
    """
    if not isinstance(changes, list):
        raise SorterError("changes must be a list")
    breaking = [c for c in changes if is_breaking(c)]
    non_breaking = [c for c in changes if not is_breaking(c)]
    return breaking + non_breaking


def sort_by_change_type(changes: List[SchemaChange]) -> List[SchemaChange]:
    """Sort changes by change type priority (most destructive first)."""
    if not isinstance(changes, list):
        raise SorterError("changes must be a list")
    return sorted(changes, key=_change_priority)


def sort_by_table(changes: List[SchemaChange], reverse: bool = False) -> List[SchemaChange]:
    """Sort changes alphabetically by table name."""
    if not isinstance(changes, list):
        raise SorterError("changes must be a list")
    return sorted(changes, key=lambda c: (c.table or ""), reverse=reverse)


def sort_changes(
    changes: List[SchemaChange],
    primary: str = "severity",
    secondary: Optional[str] = None,
) -> List[SchemaChange]:
    """Sort changes by a primary key and optional secondary key.

    Args:
        changes: List of SchemaChange objects.
        primary: One of 'severity', 'change_type', 'table'.
        secondary: Optional second sort key (same options).

    Returns:
        Sorted list of SchemaChange objects.
    """
    _sorters = {
        "severity": sort_by_severity,
        "change_type": sort_by_change_type,
        "table": sort_by_table,
    }
    if primary not in _sorters:
        raise SorterError(f"Unknown sort key: '{primary}'. Choose from {list(_sorters)}.")
    result = _sorters[primary](changes)
    if secondary:
        if secondary not in _sorters:
            raise SorterError(f"Unknown secondary sort key: '{secondary}'. Choose from {list(_sorters)}.")
        if secondary != primary:
            result = _sorters[secondary](result)
    return result
