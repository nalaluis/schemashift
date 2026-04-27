"""Baseline management: save and load schema snapshots for comparison."""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from schemashift.loader import load_schema_from_dict, SchemaLoadError

BASELINE_VERSION = "1"


class BaselineError(Exception):
    """Raised when a baseline operation fails."""


def save_baseline(schema: dict, path: str, label: Optional[str] = None) -> None:
    """Persist a schema snapshot to a JSON baseline file."""
    payload = {
        "version": BASELINE_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "label": label or "",
        "schema": schema,
    }
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
    except OSError as exc:
        raise BaselineError(f"Could not write baseline to '{path}': {exc}") from exc


def load_baseline(path: str) -> dict:
    """Load and validate a schema snapshot from a baseline file."""
    if not os.path.exists(path):
        raise BaselineError(f"Baseline file not found: '{path}'")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"Could not read baseline '{path}': {exc}") from exc

    if not isinstance(payload, dict) or "schema" not in payload:
        raise BaselineError(f"Invalid baseline format in '{path}'.")

    try:
        schema = load_schema_from_dict(payload["schema"])
    except SchemaLoadError as exc:
        raise BaselineError(f"Baseline schema validation failed: {exc}") from exc

    return schema


def baseline_metadata(path: str) -> dict:
    """Return metadata (version, created_at, label) from a baseline file."""
    if not os.path.exists(path):
        raise BaselineError(f"Baseline file not found: '{path}'")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"Could not read baseline '{path}': {exc}") from exc

    return {
        "version": payload.get("version", "unknown"),
        "created_at": payload.get("created_at", ""),
        "label": payload.get("label", ""),
    }
