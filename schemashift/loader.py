"""Schema loader module for reading database schema definitions from various sources."""

import json
from pathlib import Path
from typing import Union


class SchemaLoadError(Exception):
    """Raised when a schema cannot be loaded or parsed."""
    pass


def load_schema_from_file(path: Union[str, Path]) -> dict:
    """Load a schema definition from a JSON file.

    Args:
        path: Path to the JSON schema file.

    Returns:
        A dictionary representing the schema.

    Raises:
        SchemaLoadError: If the file cannot be read or parsed.
    """
    path = Path(path)
    if not path.exists():
        raise SchemaLoadError(f"Schema file not found: {path}")
    if path.suffix.lower() != ".json":
        raise SchemaLoadError(f"Unsupported file format '{path.suffix}'. Only .json is supported.")
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise SchemaLoadError(f"Failed to parse JSON schema from '{path}': {e}") from e
    return _validate_schema_structure(data, source=str(path))


def load_schema_from_dict(data: dict) -> dict:
    """Load and validate a schema from an already-parsed dictionary.

    Args:
        data: Raw schema dictionary.

    Returns:
        Validated schema dictionary.

    Raises:
        SchemaLoadError: If the dictionary does not conform to the expected structure.
    """
    if not isinstance(data, dict):
        raise SchemaLoadError("Schema must be a JSON object (dict).")
    return _validate_schema_structure(data, source="<dict>")


def _validate_schema_structure(data: dict, source: str) -> dict:
    """Validate that the schema dictionary has the expected top-level structure.

    Expected structure:
        {
            "tables": {
                "<table_name>": {
                    "columns": {"<col>": {"type": "...", ...}},
                    "indexes": {"<idx>": {"columns": [...], ...}}  # optional
                }
            }
        }
    """
    if "tables" not in data:
        raise SchemaLoadError(f"Schema from '{source}' is missing required key 'tables'.")
    if not isinstance(data["tables"], dict):
        raise SchemaLoadError(f"Schema from '{source}': 'tables' must be a JSON object.")
    for table_name, table_def in data["tables"].items():
        if not isinstance(table_def, dict):
            raise SchemaLoadError(
                f"Schema from '{source}': table '{table_name}' definition must be a JSON object."
            )
        if "columns" not in table_def:
            raise SchemaLoadError(
                f"Schema from '{source}': table '{table_name}' is missing required key 'columns'."
            )
        if not isinstance(table_def["columns"], dict):
            raise SchemaLoadError(
                f"Schema from '{source}': table '{table_name}'.columns must be a JSON object."
            )
    return data
