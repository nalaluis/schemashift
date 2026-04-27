"""Filter schema changes by severity, type, or affected table."""

from typing import List, Optional
from schemashift.comparator import SchemaChange, ChangeType
from schemashift.differ import is_breaking


class FilterError(Exception):
    """Raised when filter configuration is invalid."""


VALID_SEVERITIES = {"breaking", "non-breaking"}


def filter_changes(
    changes: List[SchemaChange],
    *,
    severity: Optional[str] = None,
    change_types: Optional[List[str]] = None,
    tables: Optional[List[str]] = None,
) -> List[SchemaChange]:
    """Return a filtered subset of schema changes.

    Args:
        changes: List of SchemaChange objects to filter.
        severity: If given, must be 'breaking' or 'non-breaking'.
        change_types: If given, only include changes whose ChangeType name is in this list.
        tables: If given, only include changes affecting one of these table names.

    Returns:
        Filtered list of SchemaChange objects.

    Raises:
        FilterError: If any filter argument is invalid.
    """
    if severity is not None and severity not in VALID_SEVERITIES:
        raise FilterError(
            f"Invalid severity {severity!r}. Must be one of {sorted(VALID_SEVERITIES)}."
        )

    if change_types is not None:
        valid_type_names = {ct.name for ct in ChangeType}
        unknown = set(change_types) - valid_type_names
        if unknown:
            raise FilterError(
                f"Unknown change type(s): {sorted(unknown)}. "
                f"Valid types: {sorted(valid_type_names)}."
            )

    result = changes

    if severity == "breaking":
        result = [c for c in result if is_breaking(c)]
    elif severity == "non-breaking":
        result = [c for c in result if not is_breaking(c)]

    if change_types is not None:
        allowed = set(change_types)
        result = [c for c in result if c.change_type.name in allowed]

    if tables is not None:
        allowed_tables = set(tables)
        result = [c for c in result if c.table in allowed_tables]

    return result


def partition_by_severity(
    changes: List[SchemaChange],
) -> dict:
    """Split changes into breaking and non-breaking buckets.

    Returns:
        Dict with keys 'breaking' and 'non_breaking', each a list.
    """
    breaking = [c for c in changes if is_breaking(c)]
    non_breaking = [c for c in changes if not is_breaking(c)]
    return {"breaking": breaking, "non_breaking": non_breaking}
