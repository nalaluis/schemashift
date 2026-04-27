"""Output formatters for schema change reports."""

from __future__ import annotations

import json
from typing import List

from schemashift.comparator import SchemaChange
from schemashift.differ import is_breaking, format_change


SUPPORTED_FORMATS = ("text", "json", "markdown")


class FormatterError(Exception):
    """Raised when an unsupported format is requested."""


def _severity(change: SchemaChange) -> str:
    return "BREAKING" if is_breaking(change) else "non-breaking"


def format_as_text(changes: List[SchemaChange]) -> str:
    """Render changes as plain text."""
    if not changes:
        return "No schema changes detected."
    lines = [f"Schema diff — {len(changes)} change(s) found:", ""]
    for change in changes:
        lines.append(f"  [{_severity(change)}] {format_change(change)}")
    return "\n".join(lines)


def format_as_json(changes: List[SchemaChange]) -> str:
    """Render changes as a JSON string."""
    payload = [
        {
            "change_type": change.change_type.value,
            "table": change.table,
            "column": change.column,
            "detail": change.detail,
            "breaking": is_breaking(change),
        }
        for change in changes
    ]
    return json.dumps({"changes": payload, "total": len(payload)}, indent=2)


def format_as_markdown(changes: List[SchemaChange]) -> str:
    """Render changes as a Markdown table."""
    if not changes:
        return "_No schema changes detected._"
    lines = [
        "## Schema Changes",
        "",
        "| Severity | Change Type | Table | Column | Detail |",
        "|----------|-------------|-------|--------|--------|",
    ]
    for change in changes:
        sev = _severity(change)
        col = change.column or ""
        detail = change.detail or ""
        lines.append(
            f"| {sev} | {change.change_type.value} | {change.table} | {col} | {detail} |"
        )
    return "\n".join(lines)


def render(changes: List[SchemaChange], fmt: str = "text") -> str:
    """Dispatch to the appropriate formatter.

    Args:
        changes: List of SchemaChange objects.
        fmt: One of 'text', 'json', or 'markdown'.

    Returns:
        Formatted string representation of the changes.

    Raises:
        FormatterError: If *fmt* is not supported.
    """
    if fmt == "text":
        return format_as_text(changes)
    if fmt == "json":
        return format_as_json(changes)
    if fmt == "markdown":
        return format_as_markdown(changes)
    raise FormatterError(
        f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
    )
