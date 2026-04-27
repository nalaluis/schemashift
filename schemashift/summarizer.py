"""Summarizer module for producing human-readable summaries of schema diffs."""

from dataclasses import dataclass
from typing import List

from schemashift.comparator import SchemaChange
from schemashift.differ import is_breaking


class SummarizerError(Exception):
    """Raised when summarization fails."""


@dataclass
class DiffSummary:
    total: int
    breaking: int
    non_breaking: int
    tables_affected: int
    change_type_counts: dict

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "breaking": self.breaking,
            "non_breaking": self.non_breaking,
            "tables_affected": self.tables_affected,
            "change_type_counts": self.change_type_counts,
        }


def summarize(changes: List[SchemaChange]) -> DiffSummary:
    """Produce a DiffSummary from a list of SchemaChange objects."""
    if not isinstance(changes, list):
        raise SummarizerError("changes must be a list of SchemaChange objects")

    total = len(changes)
    breaking = sum(1 for c in changes if is_breaking(c))
    non_breaking = total - breaking

    tables_affected = len({c.table for c in changes if c.table})

    change_type_counts: dict = {}
    for c in changes:
        key = c.change_type.value
        change_type_counts[key] = change_type_counts.get(key, 0) + 1

    return DiffSummary(
        total=total,
        breaking=breaking,
        non_breaking=non_breaking,
        tables_affected=tables_affected,
        change_type_counts=change_type_counts,
    )


def format_summary(summary: DiffSummary) -> str:
    """Return a plain-text representation of a DiffSummary."""
    lines = [
        "Schema Diff Summary",
        "===================",
        f"Total changes    : {summary.total}",
        f"Breaking         : {summary.breaking}",
        f"Non-breaking     : {summary.non_breaking}",
        f"Tables affected  : {summary.tables_affected}",
        "Change breakdown :",
    ]
    for change_type, count in sorted(summary.change_type_counts.items()):
        lines.append(f"  {change_type:<30} {count}")
    return "\n".join(lines)
