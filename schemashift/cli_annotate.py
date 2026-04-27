"""CLI sub-command: annotate — print migration hints for detected changes."""

import argparse
import json
import sys

from schemashift.loader import load_schema_from_file
from schemashift.comparator import compare_schemas
from schemashift.annotator import annotate_all, AnnotatorError


def add_annotate_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'annotate' sub-command on an existing subparsers object."""
    parser = subparsers.add_parser(
        "annotate",
        help="Show migration hints for schema changes between two schema files.",
    )
    parser.add_argument("old_schema", help="Path to the old schema JSON file.")
    parser.add_argument("new_schema", help="Path to the new schema JSON file.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.set_defaults(func=run_annotate)


def run_annotate(args: argparse.Namespace) -> int:
    """Execute the annotate sub-command. Returns exit code."""
    try:
        old = load_schema_from_file(args.old_schema)
        new = load_schema_from_file(args.new_schema)
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading schema: {exc}", file=sys.stderr)
        return 1

    changes = compare_schemas(old, new)

    if not changes:
        print("No schema changes detected.")
        return 0

    try:
        annotated = annotate_all(changes)
    except AnnotatorError as exc:
        print(f"Annotation error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(annotated, indent=2))
    else:
        for entry in annotated:
            breaking_label = "[BREAKING]" if entry["breaking"] else "[non-breaking]"
            print(f"{breaking_label} {entry['change']}")
            print(f"  Hint: {entry['hint']}")
            print()

    return 0
