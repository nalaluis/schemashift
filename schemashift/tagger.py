"""Tag schema changes with custom labels for categorization and tracking."""

from typing import List, Dict, Optional
from schemashift.comparator import SchemaChange, ChangeType


class TaggerError(Exception):
    """Raised when tagging operations fail."""


# Default tags assigned to each ChangeType
_DEFAULT_TAGS: Dict[ChangeType, List[str]] = {
    ChangeType.TABLE_REMOVED: ["destructive", "data-loss"],
    ChangeType.TABLE_ADDED: ["additive"],
    ChangeType.COLUMN_REMOVED: ["destructive", "data-loss"],
    ChangeType.COLUMN_ADDED: ["additive"],
    ChangeType.COLUMN_TYPE_CHANGED: ["breaking", "type-change"],
    ChangeType.INDEX_REMOVED: ["performance", "breaking"],
    ChangeType.INDEX_ADDED: ["performance", "additive"],
    ChangeType.CONSTRAINT_REMOVED: ["breaking", "integrity"],
    ChangeType.CONSTRAINT_ADDED: ["additive", "integrity"],
}


def tag_change(
    change: SchemaChange,
    extra_tags: Optional[List[str]] = None,
) -> List[str]:
    """Return tags for a single SchemaChange.

    Combines default tags for the change type with any caller-supplied
    extra_tags.  Duplicate tags are removed while preserving order.
    """
    if not isinstance(change, SchemaChange):
        raise TaggerError(f"Expected SchemaChange, got {type(change).__name__}")

    base = list(_DEFAULT_TAGS.get(change.change_type, []))
    for tag in extra_tags or []:
        if not isinstance(tag, str):
            raise TaggerError(f"Tags must be strings, got {type(tag).__name__}")
        if tag not in base:
            base.append(tag)
    return base


def tag_all(
    changes: List[SchemaChange],
    extra_tags: Optional[List[str]] = None,
) -> Dict[str, List[str]]:
    """Return a mapping of change description -> tags for every change.

    The key is the string representation of the SchemaChange so results
    can be serialised easily.
    """
    if not isinstance(changes, list):
        raise TaggerError("changes must be a list")
    return {str(c): tag_change(c, extra_tags) for c in changes}


def filter_by_tag(
    changes: List[SchemaChange],
    tag: str,
) -> List[SchemaChange]:
    """Return only the changes whose default tag set includes *tag*."""
    if not isinstance(tag, str) or not tag:
        raise TaggerError("tag must be a non-empty string")
    return [c for c in changes if tag in tag_change(c)]
