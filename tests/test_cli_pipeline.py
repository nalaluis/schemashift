"""Tests for schemashift.cli_pipeline."""

import json
import pytest
from unittest.mock import patch, MagicMock

from schemashift.cli_pipeline import run_pipeline_cmd
from schemashift.comparator import SchemaChange, ChangeType
from schemashift.loader import SchemaLoadError
from schemashift.differ_pipeline import PipelineResult
from schemashift.scorer import DiffScore


def _args(**kwargs):
    defaults = {
        "old_schema": "old.json",
        "new_schema": "new.json",
        "severity": None,
        "no_deduplicate": False,
        "no_sort": False,
        "no_tag": False,
        "tags": [],
    }
    defaults.update(kwargs)
    return MagicMock(**defaults)


def _make_score(breaking: bool = False) -> DiffScore:
    return DiffScore(total=10 if breaking else 0, breaking_count=1 if breaking else 0,
                     has_breaking=breaking, risk_level="high" if breaking else "low")


@patch("schemashift.cli_pipeline.load_schema_from_file", side_effect=SchemaLoadError("bad"))
def test_load_error_returns_2(mock_load, capsys):
    code = run_pipeline_cmd(_args())
    assert code == 2
    captured = capsys.readouterr()
    assert "Error loading schema" in captured.err


@patch("schemashift.cli_pipeline.compare_schemas", return_value=[])
@patch("schemashift.cli_pipeline.load_schema_from_file", return_value={})
@patch("schemashift.cli_pipeline.run_pipeline")
def test_no_breaking_returns_0(mock_pipeline, mock_load, mock_compare, capsys):
    mock_pipeline.return_value = PipelineResult(changes=[], score=_make_score(False))
    code = run_pipeline_cmd(_args())
    assert code == 0


@patch("schemashift.cli_pipeline.compare_schemas", return_value=[])
@patch("schemashift.cli_pipeline.load_schema_from_file", return_value={})
@patch("schemashift.cli_pipeline.run_pipeline")
def test_breaking_returns_1(mock_pipeline, mock_load, mock_compare, capsys):
    mock_pipeline.return_value = PipelineResult(changes=[], score=_make_score(True))
    code = run_pipeline_cmd(_args())
    assert code == 1


@patch("schemashift.cli_pipeline.compare_schemas", return_value=[])
@patch("schemashift.cli_pipeline.load_schema_from_file", return_value={})
@patch("schemashift.cli_pipeline.run_pipeline")
def test_output_is_valid_json(mock_pipeline, mock_load, mock_compare, capsys):
    mock_pipeline.return_value = PipelineResult(
        changes=[], score=_make_score(False)
    )
    mock_pipeline.return_value.as_dict = lambda: {"changes": [], "score": {}}
    run_pipeline_cmd(_args())
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "changes" in parsed
