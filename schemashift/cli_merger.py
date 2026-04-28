"""CLI subcommand for merging multiple diff outputs."""

import argparse
import json
from typing import List

from schemashift.loader import load_schema_from_file
from schemashift.comparator import compare_schemas
from schemashift.merger import merge_diffs, MergerError
from schemashift.formatter import format_as_text, format_as_json, format_as_markdown


def add_merger_subcommand(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'merge' subcommand."""
    parser = subparsers.add_parser(
        "merge",
        help="Merge diffs from multiple schema pairs and report unified changes.",
    )
    parser.add_argument(
        "--pairs",
        nargs="+",
        metavar="OLD:NEW",
        required=True,
        help="Pairs of schema files in OLD:NEW format.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text).",
    )
    parser.set_defaults(func=run_merger)


def run_merger(args: argparse.Namespace) -> int:
    """Execute the merge subcommand.

    Returns:
        Exit code: 1 if breaking changes found, 0 otherwise.
    """
    diffs = []
    for pair in args.pairs:
        if ":" not in pair:
            print(f"[error] Invalid pair format '{pair}', expected OLD:NEW")
            return 2
        old_path, new_path = pair.split(":", 1)
        try:
            old_schema = load_schema_from_file(old_path)
            new_schema = load_schema_from_file(new_path)
        except Exception as exc:
            print(f"[error] Failed to load schemas for pair '{pair}': {exc}")
            return 2
        diffs.append(compare_schemas(old_schema, new_schema))

    try:
        merged = merge_diffs(*diffs)
    except MergerError as exc:
        print(f"[error] Merge failed: {exc}")
        return 2

    fmt = args.format
    if fmt == "json":
        print(format_as_json(merged))
    elif fmt == "markdown":
        print(format_as_markdown(merged))
    else:
        print(format_as_text(merged))

    return 1 if any(True for c in merged if c.breaking) else 0
