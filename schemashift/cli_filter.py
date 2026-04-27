"""CLI subcommand: filter — print schema changes matching given criteria."""

import argparse
import json
import sys

from schemashift.loader import load_schema_from_file
from schemashift.comparator import compare_schemas
from schemashift.filter import filter_changes, FilterError
from schemashift.differ import format_change


def add_filter_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'filter' subcommand on *subparsers*."""
    parser = subparsers.add_parser(
        "filter",
        help="Compare two schemas and display only matching changes.",
    )
    parser.add_argument("old", help="Path to the old schema JSON file.")
    parser.add_argument("new", help="Path to the new schema JSON file.")
    parser.add_argument(
        "--severity",
        choices=["breaking", "non-breaking"],
        default=None,
        help="Only show changes of this severity.",
    )
    parser.add_argument(
        "--type",
        dest="change_types",
        nargs="+",
        metavar="CHANGE_TYPE",
        default=None,
        help="Only show changes of these ChangeType names (e.g. COLUMN_REMOVED).",
    )
    parser.add_argument(
        "--table",
        dest="tables",
        nargs="+",
        metavar="TABLE",
        default=None,
        help="Only show changes affecting these tables.",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output results as JSON.",
    )
    parser.set_defaults(func=run_filter)


def run_filter(args: argparse.Namespace) -> int:
    """Execute the filter subcommand. Returns exit code."""
    try:
        old_schema = load_schema_from_file(args.old)
        new_schema = load_schema_from_file(args.new)
    except Exception as exc:  # pragma: no cover
        print(f"Error loading schema: {exc}", file=sys.stderr)
        return 1

    changes = compare_schemas(old_schema, new_schema)

    try:
        filtered = filter_changes(
            changes,
            severity=args.severity,
            change_types=args.change_types,
            tables=args.tables,
        )
    except FilterError as exc:
        print(f"Filter error: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        output = [
            {"table": c.table, "change_type": c.change_type.name, "description": str(c)}
            for c in filtered
        ]
        print(json.dumps(output, indent=2))
    else:
        if not filtered:
            print("No changes match the given filters.")
        else:
            for change in filtered:
                print(format_change(change))

    return 0
