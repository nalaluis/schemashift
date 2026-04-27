"""CLI helper that adds a 'summary' sub-command to the schemashift CLI."""

import json
import sys
from argparse import ArgumentParser, Namespace

from schemashift.comparator import compare_schemas
from schemashift.loader import SchemaLoadError, load_schema_from_file
from schemashift.summarizer import SummarizerError, format_summary, summarize


def add_summary_subcommand(subparsers) -> None:
    """Register the 'summary' sub-command onto an existing subparsers group."""
    parser: ArgumentParser = subparsers.add_parser(
        "summary",
        help="Print a concise summary of breaking and non-breaking changes.",
    )
    parser.add_argument("old_schema", help="Path to the old schema JSON file.")
    parser.add_argument("new_schema", help="Path to the new schema JSON file.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.set_defaults(func=run_summary)


def run_summary(args: Namespace) -> int:
    """Execute the summary sub-command. Returns an exit code."""
    try:
        old = load_schema_from_file(args.old_schema)
        new = load_schema_from_file(args.new_schema)
    except SchemaLoadError as exc:
        print(f"Error loading schema: {exc}", file=sys.stderr)
        return 1

    try:
        changes = compare_schemas(old, new)
        summary = summarize(changes)
    except SummarizerError as exc:
        print(f"Summarization error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(summary.as_dict(), indent=2))
    else:
        print(format_summary(summary))

    return 1 if summary.breaking > 0 else 0
