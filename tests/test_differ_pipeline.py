"""Tests for schemashift.differ_pipeline."""

import pytest

from schemashift.comparator import SchemaChange, ChangeType
from schemashift.differ_pipeline import (
    run_pipeline,
    PipelineConfig,
    PipelineError,
    PipelineResult,
)


def _make(change_type: ChangeType, table: str = "users", detail: str = "") -> SchemaChange:
    return SchemaChange(change_type=change_type, table=table, detail=detail)


def test_run_pipeline_empty_list():
    result = run_pipeline([])
    assert isinstance(result, PipelineResult)
    assert result.changes == []
    assert result.score.total == 0


def test_run_pipeline_default_config_returns_all_changes():
    changes = [
        _make(ChangeType.COLUMN_ADDED),
        _make(ChangeType.TABLE_REMOVED),
    ]
    result = run_pipeline(changes)
    assert len(result.changes) == 2


def test_run_pipeline_severity_filter_breaking_only():
    changes = [
        _make(ChangeType.COLUMN_ADDED),
        _make(ChangeType.TABLE_REMOVED),
        _make(ChangeType.COLUMN_REMOVED),
    ]
    config = PipelineConfig(severity_filter="breaking")
    result = run_pipeline(changes, config)
    breaking_types = {ChangeType.TABLE_REMOVED, ChangeType.COLUMN_REMOVED}
    for c in result.changes:
        assert c.change_type in breaking_types


def test_run_pipeline_invalid_severity_raises():
    with pytest.raises(PipelineError, match="severity_filter"):
        run_pipeline([], PipelineConfig(severity_filter="unknown"))


def test_run_pipeline_invalid_input_raises():
    with pytest.raises(PipelineError):
        run_pipeline("not a list")  # type: ignore


def test_run_pipeline_deduplicates_by_default():
    c = _make(ChangeType.TABLE_REMOVED, table="orders")
    result = run_pipeline([c, c])
    assert len(result.changes) == 1


def test_run_pipeline_no_deduplicate_keeps_duplicates():
    c = _make(ChangeType.TABLE_REMOVED, table="orders")
    config = PipelineConfig(deduplicate=False)
    result = run_pipeline([c, c], config)
    assert len(result.changes) == 2


def test_run_pipeline_sort_breaking_first():
    changes = [
        _make(ChangeType.COLUMN_ADDED),
        _make(ChangeType.TABLE_REMOVED),
    ]
    result = run_pipeline(changes)
    assert result.changes[0].change_type == ChangeType.TABLE_REMOVED


def test_run_pipeline_tags_applied():
    changes = [_make(ChangeType.COLUMN_REMOVED)]
    config = PipelineConfig(tag=True, extra_tags=["reviewed"])
    result = run_pipeline(changes, config)
    tags = getattr(result.changes[0], "tags", [])
    assert "reviewed" in tags


def test_run_pipeline_score_reflects_breaking():
    changes = [_make(ChangeType.TABLE_REMOVED)]
    result = run_pipeline(changes)
    assert result.score.has_breaking is True
    assert result.score.total > 0


def test_run_pipeline_as_dict_structure():
    changes = [_make(ChangeType.COLUMN_ADDED, detail="email")]
    result = run_pipeline(changes)
    d = result.as_dict()
    assert "changes" in d
    assert "score" in d
    assert d["changes"][0]["table"] == "users"
