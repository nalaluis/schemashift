"""Diff formatting utilities for schema changes."""

from typing import List
from schemashift.comparator import SchemaChange, ChangeType


ANSI_RED = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_GREEN = "\033[92m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"

_SEVERITY_COLORS = {
    ChangeType.TABLE_REMOVED: ANSI_RED,
    ChangeType.COLUMN_REMOVED: ANSI_RED,
    ChangeType.COLUMN_TYPE_CHANGED: ANSI_YELLOW,
    ChangeType.INDEX_REMOVED: ANSI_YELLOW,
    ChangeType.TABLE_ADDED: ANSI_GREEN,
    ChangeType.COLUMN_ADDED: ANSI_GREEN,
    ChangeType.INDEX_ADDED: ANSI_GREEN,
}

_BREAKING_TYPES = {
    ChangeType.TABLE_REMOVED,
    ChangeType.COLUMN_REMOVED,
    ChangeType.COLUMN_TYPE_CHANGED,
    ChangeType.INDEX_REMOVED,
}


def is_breaking(change: SchemaChange) -> bool:
    """Return True if the change is considered breaking."""
    return change.change_type in _BREAKING_TYPES


def format_change(change: SchemaChange, color: bool = False) -> str:
    """Format a single SchemaChange as a human-readable string."""
    prefix = "[BREAKING] " if is_breaking(change) else "[non-breaking] "
    line = f"{prefix}{change}"
    if color:
        color_code = _SEVERITY_COLORS.get(change.change_type, "")
        line = f"{color_code}{line}{ANSI_RESET}"
    return line


def format_diff(changes: List[SchemaChange], color: bool = False) -> str:
    """Format a list of SchemaChanges as a diff-style summary string."""
    if not changes:
        return "No schema changes detected."

    breaking = [c for c in changes if is_breaking(c)]
    non_breaking = [c for c in changes if not is_breaking(c)]

    lines = []
    header = f"Schema Diff: {len(changes)} change(s) ({len(breaking)} breaking)"
    if color:
        header = f"{ANSI_BOLD}{header}{ANSI_RESET}"
    lines.append(header)
    lines.append("-" * len(header))

    for change in breaking + non_breaking:
        lines.append(format_change(change, color=color))

    return "\n".join(lines)


def count_breaking(changes: List[SchemaChange]) -> int:
    """Return the number of breaking changes in the list."""
    return sum(1 for c in changes if is_breaking(c))
