"""Deduplicator: remove duplicate SchemaChange entries from a diff list."""

from typing import List, Tuple
from schemashift.comparator import SchemaChange


class DeduplicatorError(Exception):
    """Raised when deduplication encounters invalid input."""


def _change_key(change: SchemaChange) -> Tuple:
    """Return a hashable key that uniquely identifies a change."""
    return (
        change.change_type,
        change.table,
        change.column,
        change.old_value,
        change.new_value,
    )


def deduplicate(changes: List[SchemaChange]) -> List[SchemaChange]:
    """Return a new list with duplicate SchemaChange entries removed.

    Order of first occurrence is preserved.

    Args:
        changes: List of SchemaChange objects, possibly containing duplicates.

    Returns:
        List of unique SchemaChange objects.

    Raises:
        DeduplicatorError: If *changes* is not a list or contains non-SchemaChange items.
    """
    if not isinstance(changes, list):
        raise DeduplicatorError("changes must be a list")

    seen = set()
    result: List[SchemaChange] = []
    for idx, change in enumerate(changes):
        if not isinstance(change, SchemaChange):
            raise DeduplicatorError(
                f"Item at index {idx} is not a SchemaChange instance"
            )
        key = _change_key(change)
        if key not in seen:
            seen.add(key)
            result.append(change)
    return result


def count_duplicates(changes: List[SchemaChange]) -> int:
    """Return the number of duplicate entries in *changes*.

    Args:
        changes: List of SchemaChange objects.

    Returns:
        Number of entries that would be removed by :func:`deduplicate`.
    """
    if not isinstance(changes, list):
        raise DeduplicatorError("changes must be a list")
    return len(changes) - len(deduplicate(changes))
