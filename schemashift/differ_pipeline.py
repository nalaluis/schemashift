"""Pipeline for chaining diff transformations (filter, sort, deduplicate, tag, score)."""

from dataclasses import dataclass, field
from typing import List, Optional

from schemashift.comparator import SchemaChange
from schemashift.filter import filter_changes
from schemashift.sorter import sort_by_severity
from schemashift.deduplicator import deduplicate
from schemashift.tagger import tag_all
from schemashift.scorer import score_diff, DiffScore


class PipelineError(Exception):
    """Raised when the pipeline encounters a configuration or runtime error."""


@dataclass
class PipelineConfig:
    severity_filter: Optional[str] = None   # "breaking" | "non_breaking" | None
    deduplicate: bool = True
    sort: bool = True
    tag: bool = True
    extra_tags: List[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    changes: List[SchemaChange]
    score: DiffScore

    def as_dict(self) -> dict:
        return {
            "changes": [
                {
                    "change_type": c.change_type.value,
                    "table": c.table,
                    "detail": c.detail,
                    "tags": getattr(c, "tags", []),
                }
                for c in self.changes
            ],
            "score": self.score.as_dict(),
        }


def run_pipeline(changes: List[SchemaChange], config: Optional[PipelineConfig] = None) -> PipelineResult:
    """Apply a configurable sequence of transformations to a list of SchemaChange objects."""
    if not isinstance(changes, list):
        raise PipelineError("changes must be a list of SchemaChange objects")

    if config is None:
        config = PipelineConfig()

    result = list(changes)

    if config.severity_filter:
        valid = {"breaking", "non_breaking"}
        if config.severity_filter not in valid:
            raise PipelineError(f"severity_filter must be one of {valid}")
        result = filter_changes(result, severity=config.severity_filter)

    if config.deduplicate:
        result = deduplicate(result)

    if config.sort:
        result = sort_by_severity(result)

    if config.tag:
        result = tag_all(result, extra_tags=config.extra_tags)

    score = score_diff(result)
    return PipelineResult(changes=result, score=score)
