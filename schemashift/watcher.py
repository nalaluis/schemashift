"""Schema watcher: detect changes between a saved baseline and a current schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from schemashift.baseline import load_baseline, BaselineError
from schemashift.comparator import SchemaChange, compare_schemas
from schemashift.differ import is_breaking, count_breaking
from schemashift.loader import load_schema_from_dict


class WatcherError(Exception):
    """Raised when the watcher encounters an unrecoverable problem."""


@dataclass
class WatchResult:
    """Result produced by :func:`watch`."""

    changes: List[SchemaChange] = field(default_factory=list)
    breaking_count: int = 0
    baseline_path: Optional[str] = None
    has_changes: bool = False

    @property
    def is_clean(self) -> bool:
        """Return True when no changes were detected."""
        return not self.has_changes


def watch(baseline_path: str | Path, current_schema: dict) -> WatchResult:
    """Compare *current_schema* against the baseline stored at *baseline_path*.

    Parameters
    ----------
    baseline_path:
        Filesystem path to a previously saved baseline JSON file.
    current_schema:
        A schema dict as produced by :func:`~schemashift.loader.load_schema_from_dict`.

    Returns
    -------
    WatchResult
        Populated with all detected :class:`~schemashift.comparator.SchemaChange` objects.

    Raises
    ------
    WatcherError
        If the baseline cannot be loaded or the schema is invalid.
    """
    path = Path(baseline_path)
    try:
        baseline_data = load_baseline(path)
    except BaselineError as exc:
        raise WatcherError(f"Could not load baseline: {exc}") from exc

    try:
        old_schema = load_schema_from_dict(baseline_data)
        new_schema = load_schema_from_dict(current_schema)
    except Exception as exc:  # noqa: BLE001
        raise WatcherError(f"Schema validation failed: {exc}") from exc

    changes = compare_schemas(old_schema, new_schema)
    breaking = count_breaking(changes)

    return WatchResult(
        changes=changes,
        breaking_count=breaking,
        baseline_path=str(path),
        has_changes=bool(changes),
    )
