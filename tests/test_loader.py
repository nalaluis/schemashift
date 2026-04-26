"""Tests for schemashift.loader module."""

import json
import pytest
from pathlib import Path

from schemashift.loader import load_schema_from_dict, load_schema_from_file, SchemaLoadError


VALID_SCHEMA = {
    "tables": {
        "users": {
            "columns": {
                "id": {"type": "integer", "nullable": False},
                "email": {"type": "varchar(255)", "nullable": False},
            },
            "indexes": {
                "idx_users_email": {"columns": ["email"], "unique": True}
            },
        }
    }
}


# --- load_schema_from_dict ---

def test_load_schema_from_dict_valid():
    schema = load_schema_from_dict(VALID_SCHEMA)
    assert "tables" in schema
    assert "users" in schema["tables"]


def test_load_schema_from_dict_not_a_dict():
    with pytest.raises(SchemaLoadError, match="must be a JSON object"):
        load_schema_from_dict(["not", "a", "dict"])


def test_load_schema_from_dict_missing_tables_key():
    with pytest.raises(SchemaLoadError, match="missing required key 'tables'"):
        load_schema_from_dict({"views": {}})


def test_load_schema_from_dict_tables_not_dict():
    with pytest.raises(SchemaLoadError, match="'tables' must be a JSON object"):
        load_schema_from_dict({"tables": "not_a_dict"})


def test_load_schema_from_dict_table_missing_columns():
    with pytest.raises(SchemaLoadError, match="missing required key 'columns'"):
        load_schema_from_dict({"tables": {"users": {"indexes": {}}}})


def test_load_schema_from_dict_columns_not_dict():
    with pytest.raises(SchemaLoadError, match="columns must be a JSON object"):
        load_schema_from_dict({"tables": {"users": {"columns": ["id", "email"]}}})


def test_load_schema_from_dict_empty_tables():
    schema = load_schema_from_dict({"tables": {}})
    assert schema["tables"] == {}


# --- load_schema_from_file ---

def test_load_schema_from_file_valid(tmp_path):
    schema_file = tmp_path / "schema.json"
    schema_file.write_text(json.dumps(VALID_SCHEMA), encoding="utf-8")
    schema = load_schema_from_file(schema_file)
    assert "users" in schema["tables"]


def test_load_schema_from_file_not_found(tmp_path):
    with pytest.raises(SchemaLoadError, match="not found"):
        load_schema_from_file(tmp_path / "nonexistent.json")


def test_load_schema_from_file_wrong_extension(tmp_path):
    bad_file = tmp_path / "schema.yaml"
    bad_file.write_text("tables: {}", encoding="utf-8")
    with pytest.raises(SchemaLoadError, match="Unsupported file format"):
        load_schema_from_file(bad_file)


def test_load_schema_from_file_invalid_json(tmp_path):
    bad_json = tmp_path / "schema.json"
    bad_json.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(SchemaLoadError, match="Failed to parse JSON"):
        load_schema_from_file(bad_json)


def test_load_schema_from_file_accepts_string_path(tmp_path):
    schema_file = tmp_path / "schema.json"
    schema_file.write_text(json.dumps(VALID_SCHEMA), encoding="utf-8")
    schema = load_schema_from_file(str(schema_file))
    assert "tables" in schema
