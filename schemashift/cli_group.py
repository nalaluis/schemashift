"""CLI subcommand: group — display changes grouped by table, severity, or type."""

import argparse
import json
import sys

from schemashift.loader import load_schema_from_file, SchemaLoadError
from schemashift.comparator import compare_schemas
from schemashift.grouper import group_by_table, group_by_severity, group_by_change_type, GrouperError
from schemashift.differ import format_change


def add_group_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "group",
        help="Group detected schema changes by table, severity, or change type",
    )
    parser.add_argument("old", help="Path to the old schema JSON file")
    parser.add_argument("new", help="Path to the new schema JSON file")
    parser.add_argument(
        "--by",
        choices=["table", "severity", "type"],
        default="table",
        help="Dimension to group changes by (default: table)",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.set_defaults(func=run_group)


def run_group(args: argparse.Namespace) -> int:
    try:
        old_schema = load_schema_from_file(args.old)
        new_schema = load_schema_from_file(args.new)
    except SchemaLoadError as exc:
        print(f"Error loading schema: {exc}", file=sys.stderr)
        return 1

    changes = compare_schemas(old_schema, new_schema)

    try:
        if args.by == "table":
            groups = group_by_table(changes)
        elif args.by == "severity":
            groups = group_by_severity(changes)
        else:
            groups = group_by_change_type(changes)
    except GrouperError as exc:
        print(f"Grouping error: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        serialisable = {
            key: [format_change(c) for c in cs] for key, cs in groups.items()
        }
        print(json.dumps(serialisable, indent=2))
    else:
        for key, cs in groups.items():
            print(f"\n[{key}] ({len(cs)} change(s))")
            for c in cs:
                print(f"  - {format_change(c)}")

    return 0
