"""Tests for schemashift.formatter."""

import json
import pytest

from schemashift.comparator import ChangeType, SchemaChange
from schemashift.formatter import (
    FormatterError,
    format_as_json,
    format_as_markdown,
    format_as_text,
    render,
    SUPPORTED_FORMATS,
)


def _change(change_type, table="users", column=None, detail=None):
    return SchemaChange(change_type=change_type, table=table, column=column, detail=detail)


# --- format_as_text ---

def test_format_as_text_no_changes():
    assert format_as_text([]) == "No schema changes detected."


def test_format_as_text_contains_severity_and_description():
    change = _change(ChangeType.COLUMN_REMOVED, column="email")
    result = format_as_text([change])
    assert "BREAKING" in result
    assert "users" in result
    assert "1 change" in result


def test_format_as_text_non_breaking():
    change = _change(ChangeType.TABLE_ADDED, table="audit_log")
    result = format_as_text([change])
    assert "non-breaking" in result


# --- format_as_json ---

def test_format_as_json_structure():
    change = _change(ChangeType.COLUMN_TYPE_CHANGED, column="age", detail="int -> varchar")
    result = json.loads(format_as_json([change]))
    assert result["total"] == 1
    entry = result["changes"][0]
    assert entry["table"] == "users"
    assert entry["column"] == "age"
    assert entry["breaking"] is True
    assert entry["detail"] == "int -> varchar"


def test_format_as_json_empty():
    result = json.loads(format_as_json([]))
    assert result["total"] == 0
    assert result["changes"] == []


# --- format_as_markdown ---

def test_format_as_markdown_no_changes():
    assert "No schema changes" in format_as_markdown([])


def test_format_as_markdown_contains_table_header():
    change = _change(ChangeType.TABLE_REMOVED, table="orders")
    result = format_as_markdown([change])
    assert "| Severity |" in result
    assert "orders" in result
    assert "BREAKING" in result


def test_format_as_markdown_non_breaking_row():
    change = _change(ChangeType.COLUMN_ADDED, column="nickname")
    result = format_as_markdown([change])
    assert "non-breaking" in result


# --- render dispatcher ---

def test_render_text():
    result = render([], fmt="text")
    assert "No schema changes" in result


def test_render_json():
    result = render([], fmt="json")
    assert json.loads(result)["total"] == 0


def test_render_markdown():
    result = render([], fmt="markdown")
    assert "No schema changes" in result


def test_render_unsupported_format_raises():
    with pytest.raises(FormatterError, match="Unsupported format"):
        render([], fmt="csv")


def test_supported_formats_constant():
    assert "text" in SUPPORTED_FORMATS
    assert "json" in SUPPORTED_FORMATS
    assert "markdown" in SUPPORTED_FORMATS
