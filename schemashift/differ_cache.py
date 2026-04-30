"""differ_cache.py — Caching layer for schema diff results.

Provides a simple file-backed cache that stores the result of a diff
between two schema files, keyed by the combined hash of their contents.
This avoids re-running expensive comparisons when neither schema has
changed.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from schemashift.comparator import SchemaChange, ChangeType


class CacheError(Exception):
    """Raised when the diff cache encounters an unrecoverable problem."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hash_schema(schema: dict) -> str:
    """Return a stable SHA-256 hex digest for *schema*.

    The dict is serialised with sorted keys so that insertion order does
    not affect the digest.
    """
    raw = json.dumps(schema, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_key(old_schema: dict, new_schema: dict) -> str:
    """Combine the hashes of both schemas into a single cache key."""
    return _hash_schema(old_schema) + "-" + _hash_schema(new_schema)


def _change_to_dict(change: SchemaChange) -> dict:
    """Serialise a *SchemaChange* to a plain dict for JSON storage."""
    return {
        "change_type": change.change_type.value,
        "table": change.table,
        "column": change.column,
        "old_value": change.old_value,
        "new_value": change.new_value,
        "description": change.description,
    }


def _dict_to_change(data: dict) -> SchemaChange:
    """Deserialise a plain dict back to a *SchemaChange*."""
    return SchemaChange(
        change_type=ChangeType(data["change_type"]),
        table=data["table"],
        column=data.get("column"),
        old_value=data.get("old_value"),
        new_value=data.get("new_value"),
        description=data.get("description", ""),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def cache_path(cache_dir: str | Path, old_schema: dict, new_schema: dict) -> Path:
    """Return the file path where a diff result would be cached.

    The file is named ``<cache_key>.json`` inside *cache_dir*.
    """
    key = _cache_key(old_schema, new_schema)
    return Path(cache_dir) / f"{key}.json"


def save_to_cache(
    cache_dir: str | Path,
    old_schema: dict,
    new_schema: dict,
    changes: list[SchemaChange],
) -> Path:
    """Persist *changes* to the cache.

    Creates *cache_dir* (and any parents) if it does not already exist.
    Returns the path of the written cache file.

    Raises
    ------
    CacheError
        If the file cannot be written.
    """
    path = cache_path(cache_dir, old_schema, new_schema)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "old_hash": _hash_schema(old_schema),
            "new_hash": _hash_schema(new_schema),
            "changes": [_change_to_dict(c) for c in changes],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        raise CacheError(f"Failed to write cache file '{path}': {exc}") from exc
    return path


def load_from_cache(
    cache_dir: str | Path,
    old_schema: dict,
    new_schema: dict,
) -> list[SchemaChange] | None:
    """Load a previously cached diff result, or return *None* on a miss.

    Returns *None* (rather than raising) when the cache file does not
    exist, so callers can treat a miss as a signal to recompute.

    Raises
    ------
    CacheError
        If a cache file exists but cannot be parsed.
    """
    path = cache_path(cache_dir, old_schema, new_schema)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [_dict_to_change(d) for d in payload["changes"]]
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        raise CacheError(f"Corrupt cache file '{path}': {exc}") from exc


def invalidate_cache(cache_dir: str | Path) -> int:
    """Delete all ``*.json`` files inside *cache_dir*.

    Returns the number of files removed.  Does nothing (and returns 0)
    if *cache_dir* does not exist.
    """
    cache_dir = Path(cache_dir)
    if not cache_dir.is_dir():
        return 0
    removed = 0
    for entry in cache_dir.glob("*.json"):
        try:
            entry.unlink()
            removed += 1
        except OSError:
            pass
    return removed
