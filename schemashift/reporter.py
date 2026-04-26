"""Formats SchemaChange results into human-readable or machine-readable reports."""

import json
from typing import Literal

from schemashift.comparator import SchemaChange


def _change_to_dict(change: SchemaChange) -> dict:
    return {
        "change_type": change.change_type.value,
        "table": change.table,
        "detail": change.detail,
        "breaking": change.breaking,
        "meta": change.meta,
    }


def generate_report(
    changes: list[SchemaChange],
    fmt: Literal["text", "json", "markdown"] = "text",
) -> str:
    """Render a list of SchemaChange objects as a formatted report string."""
    if not changes:
        if fmt == "json":
            return json.dumps({"breaking_changes": 0, "changes": []}, indent=2)
        if fmt == "markdown":
            return "## SchemaShift Report\n\n✅ No breaking schema changes detected.\n"
        return "No schema changes detected.\n"

    breaking = [c for c in changes if c.breaking]
    non_breaking = [c for c in changes if not c.breaking]

    if fmt == "json":
        return json.dumps(
            {
                "breaking_changes": len(breaking),
                "non_breaking_changes": len(non_breaking),
                "changes": [_change_to_dict(c) for c in changes],
            },
            indent=2,
        )

    if fmt == "markdown":
        lines = ["## SchemaShift Report\n"]
        lines.append(f"- **Breaking changes:** {len(breaking)}")
        lines.append(f"- **Non-breaking changes:** {len(non_breaking)}\n")
        if breaking:
            lines.append("### ⚠️ Breaking Changes\n")
            for c in breaking:
                lines.append(f"- `{c.change_type.value}` — **{c.table}**: {c.detail}")
        if non_breaking:
            lines.append("\n### ℹ️ Non-Breaking Changes\n")
            for c in non_breaking:
                lines.append(f"- `{c.change_type.value}` — **{c.table}**: {c.detail}")
        return "\n".join(lines) + "\n"

    # Plain text
    lines = [f"SchemaShift Report — {len(changes)} change(s) found\n"]
    for c in changes:
        lines.append(f"  {c}")
    return "\n".join(lines) + "\n"
