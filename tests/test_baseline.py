"""Tests for schemashift.baseline module."""

import json
import os
import pytest
from schemashift.baseline import save_baseline, load_baseline, baseline_metadata, BaselineError


VALID_SCHEMA = {
    "tables": {
        "users": {
            "columns": {"id": "int", "email": "varchar"},
            "indexes": ["idx_email"],
        }
    }
}


def test_save_and_load_baseline(tmp_path):
    path = str(tmp_path / "baseline.json")
    save_baseline(VALID_SCHEMA, path, label="v1")
    schema = load_baseline(path)
    assert "tables" in schema
    assert "users" in schema["tables"]


def test_save_creates_parent_dirs(tmp_path):
    path = str(tmp_path / "nested" / "dir" / "baseline.json")
    save_baseline(VALID_SCHEMA, path)
    assert os.path.exists(path)


def test_baseline_metadata_fields(tmp_path):
    path = str(tmp_path / "baseline.json")
    save_baseline(VALID_SCHEMA, path, label="release-1.2")
    meta = baseline_metadata(path)
    assert meta["label"] == "release-1.2"
    assert meta["version"] == "1"
    assert meta["created_at"] != ""


def test_load_baseline_file_not_found(tmp_path):
    with pytest.raises(BaselineError, match="not found"):
        load_baseline(str(tmp_path / "missing.json"))


def test_load_baseline_invalid_json(tmp_path):
    path = str(tmp_path / "bad.json")
    with open(path, "w") as fh:
        fh.write("not json{{{")
    with pytest.raises(BaselineError, match="Could not read"):
        load_baseline(path)


def test_load_baseline_missing_schema_key(tmp_path):
    path = str(tmp_path / "baseline.json")
    with open(path, "w") as fh:
        json.dump({"version": "1"}, fh)
    with pytest.raises(BaselineError, match="Invalid baseline format"):
        load_baseline(path)


def test_load_baseline_invalid_schema_structure(tmp_path):
    path = str(tmp_path / "baseline.json")
    with open(path, "w") as fh:
        json.dump({"schema": {"tables": "not-a-dict"}}, fh)
    with pytest.raises(BaselineError, match="validation failed"):
        load_baseline(path)


def test_metadata_file_not_found(tmp_path):
    with pytest.raises(BaselineError, match="not found"):
        baseline_metadata(str(tmp_path / "ghost.json"))
