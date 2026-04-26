"""Core schema comparator for detecting breaking changes between two schema snapshots."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChangeType(str, Enum):
    COLUMN_REMOVED = "column_removed"
    COLUMN_TYPE_CHANGED = "column_type_changed"
    COLUMN_NULLABLE_CHANGED = "column_nullable_changed"
    TABLE_REMOVED = "table_removed"
    INDEX_REMOVED = "index_removed"
    CONSTRAINT_REMOVED = "constraint_removed"


@dataclass
class SchemaChange:
    change_type: ChangeType
    table: str
    detail: str
    breaking: bool = True
    meta: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        severity = "[BREAKING]" if self.breaking else "[non-breaking]"
        return f"{severity} {self.change_type.value} on '{self.table}': {self.detail}"


def compare_schemas(before: dict, after: dict) -> list[SchemaChange]:
    """Compare two schema dicts and return a list of detected changes.

    Each schema dict is expected in the form:
        {
            "table_name": {
                "columns": {"col_name": {"type": str, "nullable": bool}},
                "indexes": [str, ...],
                "constraints": [str, ...],
            }
        }
    """
    changes: list[SchemaChange] = []

    for table, definition in before.items():
        if table not in after:
            changes.append(
                SchemaChange(ChangeType.TABLE_REMOVED, table, f"Table '{table}' was removed.")
            )
            continue

        after_def = after[table]

        # Column-level checks
        before_cols = definition.get("columns", {})
        after_cols = after_def.get("columns", {})

        for col, col_def in before_cols.items():
            if col not in after_cols:
                changes.append(
                    SchemaChange(ChangeType.COLUMN_REMOVED, table, f"Column '{col}' was removed.")
                )
                continue

            after_col = after_cols[col]

            if col_def.get("type") != after_col.get("type"):
                changes.append(
                    SchemaChange(
                        ChangeType.COLUMN_TYPE_CHANGED,
                        table,
                        f"Column '{col}' type changed from '{col_def.get('type')}' to '{after_col.get('type')}'.",
                        meta={"before": col_def.get("type"), "after": after_col.get("type")},
                    )
                )

            if not col_def.get("nullable", True) and after_col.get("nullable", True):
                changes.append(
                    SchemaChange(
                        ChangeType.COLUMN_NULLABLE_CHANGED,
                        table,
                        f"Column '{col}' changed from NOT NULL to nullable.",
                        breaking=False,
                    )
                )

        # Index / constraint removal
        for idx in definition.get("indexes", []):
            if idx not in after_def.get("indexes", []):
                changes.append(
                    SchemaChange(ChangeType.INDEX_REMOVED, table, f"Index '{idx}' was removed.")
                )

        for constraint in definition.get("constraints", []):
            if constraint not in after_def.get("constraints", []):
                changes.append(
                    SchemaChange(
                        ChangeType.CONSTRAINT_REMOVED,
                        table,
                        f"Constraint '{constraint}' was removed.",
                    )
                )

    return changes
