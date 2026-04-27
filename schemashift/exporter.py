"""Export formatted schema-diff reports to files or stdout."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from schemashift.comparator import SchemaChange
from schemashift.formatter import render, SUPPORTED_FORMATS, FormatterError


class ExportError(Exception):
    """Raised when a report cannot be written to disk."""


def export_report(
    changes: List[SchemaChange],
    fmt: str = "text",
    output_path: Optional[str] = None,
) -> str:
    """Render *changes* and optionally write the result to *output_path*.

    Args:
        changes: List of SchemaChange objects to include in the report.
        fmt: Output format — one of ``SUPPORTED_FORMATS``.
        output_path: If given, the rendered report is written to this file.
            Parent directories are created automatically.
            If ``None`` the report is printed to *stdout*.

    Returns:
        The rendered report string.

    Raises:
        FormatterError: If *fmt* is not supported.
        ExportError: If the file cannot be written.
    """
    content = render(changes, fmt=fmt)

    if output_path is None:
        sys.stdout.write(content)
        sys.stdout.write("\n")
    else:
        path = Path(output_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise ExportError(f"Failed to write report to '{output_path}': {exc}") from exc

    return content


def available_formats() -> tuple:
    """Return the tuple of supported output format names."""
    return SUPPORTED_FORMATS
