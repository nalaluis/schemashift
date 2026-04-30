"""Tracks and queries the history of schema diffs over time."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from schemashift.comparator import SchemaChange, ChangeType


class HistoryError(Exception):
    """Raised when history operations fail."""


def _change_to_dict(change: SchemaChange) -> dict[str, Any]:
    return {
        "change_type": change.change_type.value,
        "table": change.table,
        "column": change.column,
        "detail": change.detail,
    }


def _dict_to_change(data: dict[str, Any]) -> SchemaChange:
    return SchemaChange(
        change_type=ChangeType(data["change_type"]),
        table=data["table"],
        column=data.get("column"),
        detail=data.get("detail"),
    )


def record_entry(
    path: str, changes: list[SchemaChange], label: str | None = None
) -> dict[str, Any]:
    """Append a diff entry to the history file and return the entry."""
    entry: dict[str, Any] = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "label": label or "",
        "change_count": len(changes),
        "changes": [_change_to_dict(c) for c in changes],
    }
    history = load_history(path) if os.path.exists(path) else []
    history.append(entry)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2)
    return entry


def load_history(path: str) -> list[dict[str, Any]]:
    """Load all history entries from a file."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise HistoryError(f"History file not found: {path}")
    except json.JSONDecodeError as exc:
        raise HistoryError(f"Invalid JSON in history file: {exc}") from exc
    if not isinstance(data, list):
        raise HistoryError("History file must contain a JSON array")
    return data


def query_history(
    path: str,
    *,
    label: str | None = None,
    breaking_only: bool = False,
) -> list[dict[str, Any]]:
    """Filter history entries by optional label or breaking-only flag."""
    from schemashift.differ import is_breaking

    entries = load_history(path)
    results = []
    for entry in entries:
        if label and entry.get("label") != label:
            continue
        if breaking_only:
            changes = [_dict_to_change(c) for c in entry.get("changes", [])]
            if not any(is_breaking(c) for c in changes):
                continue
        results.append(entry)
    return results
