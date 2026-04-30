"""Snapshot management: capture and compare schema snapshots over time."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from schemashift.loader import load_schema_from_dict, SchemaLoadError
from schemashift.comparator import compare_schemas, SchemaChange


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


SNAPSHOT_VERSION = 1


def take_snapshot(schema: dict[str, Any], label: str = "") -> dict[str, Any]:
    """Wrap a validated schema dict in snapshot metadata."""
    try:
        load_schema_from_dict(schema)
    except SchemaLoadError as exc:
        raise SnapshotError(f"Invalid schema: {exc}") from exc

    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "label": label,
        "captured_at": time.time(),
        "schema": schema,
    }


def save_snapshot(snapshot: dict[str, Any], path: str | Path) -> None:
    """Persist a snapshot to a JSON file, creating parent directories as needed."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        dest.write_text(json.dumps(snapshot, indent=2))
    except OSError as exc:
        raise SnapshotError(f"Cannot write snapshot to {dest}: {exc}") from exc


def load_snapshot(path: str | Path) -> dict[str, Any]:
    """Load a snapshot from a JSON file."""
    src = Path(path)
    if not src.exists():
        raise SnapshotError(f"Snapshot file not found: {src}")
    try:
        data = json.loads(src.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"Cannot read snapshot from {src}: {exc}") from exc
    if not isinstance(data, dict) or "schema" not in data:
        raise SnapshotError(f"Invalid snapshot format in {src}")
    return data


def diff_snapshots(
    old_snapshot: dict[str, Any],
    new_snapshot: dict[str, Any],
) -> list[SchemaChange]:
    """Return the list of SchemaChanges between two snapshots."""
    for key, snap in (("old", old_snapshot), ("new", new_snapshot)):
        if "schema" not in snap:
            raise SnapshotError(f"Missing 'schema' key in {key} snapshot")
    return compare_schemas(old_snapshot["schema"], new_snapshot["schema"])


def snapshot_metadata(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return metadata fields of a snapshot without the full schema."""
    return {
        "snapshot_version": snapshot.get("snapshot_version"),
        "label": snapshot.get("label", ""),
        "captured_at": snapshot.get("captured_at"),
    }
