"""Merge multiple SchemaChange lists into a unified, deduplicated diff."""

from typing import List, Dict
from schemashift.comparator import SchemaChange, ChangeType
from schemashift.deduplicator import deduplicate


class MergerError(Exception):
    """Raised when merging fails due to invalid input."""


def merge_diffs(*diffs: List[SchemaChange]) -> List[SchemaChange]:
    """Combine multiple diff lists into one deduplicated list.

    Args:
        *diffs: One or more lists of SchemaChange objects.

    Returns:
        A single deduplicated list of SchemaChange objects.

    Raises:
        MergerError: If any argument is not a list.
    """
    for i, diff in enumerate(diffs):
        if not isinstance(diff, list):
            raise MergerError(
                f"Argument at position {i} is not a list, got {type(diff).__name__}"
            )
        for j, item in enumerate(diff):
            if not isinstance(item, SchemaChange):
                raise MergerError(
                    f"Item {j} in diff {i} is not a SchemaChange, got {type(item).__name__}"
                )

    combined: List[SchemaChange] = []
    for diff in diffs:
        combined.extend(diff)

    return deduplicate(combined)


def merge_by_table(*diffs: List[SchemaChange]) -> Dict[str, List[SchemaChange]]:
    """Merge diffs and group the result by table name.

    Args:
        *diffs: One or more lists of SchemaChange objects.

    Returns:
        A dict mapping table names to their merged SchemaChange lists.
    """
    merged = merge_diffs(*diffs)
    result: Dict[str, List[SchemaChange]] = {}
    for change in merged:
        result.setdefault(change.table, []).append(change)
    return result


def count_by_source(*diffs: List[SchemaChange]) -> List[int]:
    """Return the original count of each diff before merging.

    Args:
        *diffs: One or more lists of SchemaChange objects.

    Returns:
        A list of integers representing the length of each input diff.
    """
    for i, diff in enumerate(diffs):
        if not isinstance(diff, list):
            raise MergerError(
                f"Argument at position {i} is not a list, got {type(diff).__name__}"
            )
    return [len(d) for d in diffs]
