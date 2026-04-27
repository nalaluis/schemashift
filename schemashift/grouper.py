"""Groups schema changes by table, severity, or change type."""

from collections import defaultdict
from typing import Dict, List

from schemashift.comparator import SchemaChange
from schemashift.differ import is_breaking


class GrouperError(Exception):
    """Raised when grouping fails due to invalid input."""


def group_by_table(changes: List[SchemaChange]) -> Dict[str, List[SchemaChange]]:
    """Return a mapping of table name -> list of changes affecting that table."""
    if not isinstance(changes, list):
        raise GrouperError("changes must be a list")

    groups: Dict[str, List[SchemaChange]] = defaultdict(list)
    for change in changes:
        groups[change.table].append(change)
    return dict(groups)


def group_by_severity(changes: List[SchemaChange]) -> Dict[str, List[SchemaChange]]:
    """Return a mapping of 'breaking' / 'non_breaking' -> list of changes."""
    if not isinstance(changes, list):
        raise GrouperError("changes must be a list")

    groups: Dict[str, List[SchemaChange]] = {"breaking": [], "non_breaking": []}
    for change in changes:
        key = "breaking" if is_breaking(change) else "non_breaking"
        groups[key].append(change)
    return groups


def group_by_change_type(changes: List[SchemaChange]) -> Dict[str, List[SchemaChange]]:
    """Return a mapping of change type name -> list of changes."""
    if not isinstance(changes, list):
        raise GrouperError("changes must be a list")

    groups: Dict[str, List[SchemaChange]] = defaultdict(list)
    for change in changes:
        groups[change.change_type.name].append(change)
    return dict(groups)


def group_summary(changes: List[SchemaChange]) -> Dict[str, object]:
    """Return a combined summary dict with all three grouping dimensions."""
    return {
        "by_table": {
            table: [c.change_type.name for c in cs]
            for table, cs in group_by_table(changes).items()
        },
        "by_severity": {
            severity: len(cs)
            for severity, cs in group_by_severity(changes).items()
        },
        "by_change_type": {
            ct: len(cs)
            for ct, cs in group_by_change_type(changes).items()
        },
    }
