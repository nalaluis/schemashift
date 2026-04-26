"""Tests for schemashift.comparator and schemashift.reporter."""

import json
import pytest

from schemashift.comparator import ChangeType, compare_schemas
from schemashift.reporter import generate_report


BEFORE = {
    "users": {
        "columns": {
            "id": {"type": "integer", "nullable": False},
            "email": {"type": "varchar(255)", "nullable": False},
            "age": {"type": "integer", "nullable": True},
        },
        "indexes": ["idx_users_email"],
        "constraints": ["uq_users_email"],
    },
    "orders": {
        "columns": {
            "id": {"type": "integer", "nullable": False},
            "total": {"type": "numeric(10,2)", "nullable": False},
        },
        "indexes": [],
        "constraints": [],
    },
}


def test_no_changes():
    changes = compare_schemas(BEFORE, BEFORE)
    assert changes == []


def test_table_removed():
    after = {k: v for k, v in BEFORE.items() if k != "orders"}
    changes = compare_schemas(BEFORE, after)
    assert any(c.change_type == ChangeType.TABLE_REMOVED and c.table == "orders" for c in changes)


def test_column_removed():
    import copy
    after = copy.deepcopy(BEFORE)
    del after["users"]["columns"]["age"]
    changes = compare_schemas(BEFORE, after)
    assert any(c.change_type == ChangeType.COLUMN_REMOVED and "age" in c.detail for c in changes)


def test_column_type_changed():
    import copy
    after = copy.deepcopy(BEFORE)
    after["users"]["columns"]["email"]["type"] = "text"
    changes = compare_schemas(BEFORE, after)
    type_changes = [c for c in changes if c.change_type == ChangeType.COLUMN_TYPE_CHANGED]
    assert len(type_changes) == 1
    assert type_changes[0].meta["before"] == "varchar(255)"
    assert type_changes[0].meta["after"] == "text"


def test_index_removed():
    import copy
    after = copy.deepcopy(BEFORE)
    after["users"]["indexes"] = []
    changes = compare_schemas(BEFORE, after)
    assert any(c.change_type == ChangeType.INDEX_REMOVED for c in changes)


def test_constraint_removed():
    import copy
    after = copy.deepcopy(BEFORE)
    after["users"]["constraints"] = []
    changes = compare_schemas(BEFORE, after)
    assert any(c.change_type == ChangeType.CONSTRAINT_REMOVED for c in changes)


def test_report_text_no_changes():
    report = generate_report([])
    assert "No schema changes" in report


def test_report_json_structure():
    import copy
    after = copy.deepcopy(BEFORE)
    del after["orders"]
    changes = compare_schemas(BEFORE, after)
    report = generate_report(changes, fmt="json")
    data = json.loads(report)
    assert data["breaking_changes"] >= 1
    assert isinstance(data["changes"], list)


def test_report_markdown_contains_header():
    import copy
    after = copy.deepcopy(BEFORE)
    after["users"]["columns"]["email"]["type"] = "text"
    changes = compare_schemas(BEFORE, after)
    report = generate_report(changes, fmt="markdown")
    assert "## SchemaShift Report" in report
    assert "Breaking" in report
