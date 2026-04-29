"""CLI subcommand: pipeline — run the full diff pipeline on two schema files."""

import argparse
import json
import sys

from schemashift.loader import load_schema_from_file, SchemaLoadError
from schemashift.comparator import compare_schemas
from schemashift.differ_pipeline import run_pipeline, PipelineConfig, PipelineError


def add_pipeline_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "pipeline",
        help="Run the full diff pipeline (filter → deduplicate → sort → tag → score)",
    )
    parser.add_argument("old_schema", help="Path to the old schema JSON file")
    parser.add_argument("new_schema", help="Path to the new schema JSON file")
    parser.add_argument(
        "--severity",
        choices=["breaking", "non_breaking"],
        default=None,
        help="Only include changes of this severity",
    )
    parser.add_argument(
        "--no-deduplicate", action="store_true", help="Skip deduplication step"
    )
    parser.add_argument(
        "--no-sort", action="store_true", help="Skip sorting step"
    )
    parser.add_argument(
        "--no-tag", action="store_true", help="Skip tagging step"
    )
    parser.add_argument(
        "--tags", nargs="*", default=[], help="Extra tags to attach to every change"
    )
    parser.set_defaults(func=run_pipeline_cmd)


def run_pipeline_cmd(args: argparse.Namespace) -> int:
    try:
        old = load_schema_from_file(args.old_schema)
        new = load_schema_from_file(args.new_schema)
    except SchemaLoadError as exc:
        print(f"Error loading schema: {exc}", file=sys.stderr)
        return 2

    changes = compare_schemas(old, new)

    config = PipelineConfig(
        severity_filter=args.severity,
        deduplicate=not args.no_deduplicate,
        sort=not args.no_sort,
        tag=not args.no_tag,
        extra_tags=args.tags or [],
    )

    try:
        result = run_pipeline(changes, config)
    except PipelineError as exc:
        print(f"Pipeline error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.as_dict(), indent=2))
    return 1 if result.score.has_breaking else 0
