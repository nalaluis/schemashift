"""Command-line interface for SchemaShift."""

import argparse
import json
import sys
from pathlib import Path

from schemashift.loader import load_schema_from_file, SchemaLoadError
from schemashift.comparator import compare_schemas
from schemashift.reporter import generate_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schemashift",
        description="Detect and document breaking schema changes across database migrations.",
    )
    parser.add_argument("before", type=Path, help="Path to the baseline schema JSON file.")
    parser.add_argument("after", type=Path, help="Path to the updated schema JSON file.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for the report (default: text).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write the report to a file instead of stdout.",
    )
    parser.add_argument(
        "--breaking-only",
        action="store_true",
        help="Only include breaking changes in the report.",
    )
    return parser


def run(args=None) -> int:
    """Entry point for the CLI. Returns an exit code."""
    parser = build_parser()
    parsed = parser.parse_args(args)

    try:
        before_schema = load_schema_from_file(parsed.before)
        after_schema = load_schema_from_file(parsed.after)
    except SchemaLoadError as e:
        print(f"Error loading schema: {e}", file=sys.stderr)
        return 1

    changes = compare_schemas(before_schema, after_schema)

    if parsed.breaking_only:
        changes = [c for c in changes if c.breaking]

    report = generate_report(changes, fmt=parsed.format)

    if parsed.output:
        try:
            parsed.output.write_text(report, encoding="utf-8")
            print(f"Report written to {parsed.output}")
        except OSError as e:
            print(f"Error writing report: {e}", file=sys.stderr)
            return 1
    else:
        print(report)

    return 1 if any(c.breaking for c in changes) else 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
