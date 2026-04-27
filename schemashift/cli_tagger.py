"""CLI sub-command: tag — display tags for detected schema changes."""

import argparse
import json
from typing import List

from schemashift.loader import load_schema_from_file
from schemashift.comparator import compare_schemas
from schemashift.tagger import tag_all, filter_by_tag, TaggerError


def add_tagger_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'tag' sub-command on *subparsers*."""
    parser = subparsers.add_parser(
        "tag",
        help="Show tags for each detected schema change.",
    )
    parser.add_argument("old_schema", help="Path to the old schema JSON file.")
    parser.add_argument("new_schema", help="Path to the new schema JSON file.")
    parser.add_argument(
        "--filter-tag",
        metavar="TAG",
        default=None,
        help="Only show changes that carry this tag.",
    )
    parser.add_argument(
        "--extra-tags",
        metavar="TAG",
        nargs="+",
        default=None,
        help="Additional tags to attach to every change.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output results as JSON.",
    )
    parser.set_defaults(func=run_tagger)


def run_tagger(args: argparse.Namespace) -> int:
    """Execute the 'tag' sub-command.  Returns an exit code."""
    try:
        old = load_schema_from_file(args.old_schema)
        new = load_schema_from_file(args.new_schema)
        changes = compare_schemas(old, new)

        if args.filter_tag:
            changes = filter_by_tag(changes, args.filter_tag)

        tagged = tag_all(changes, extra_tags=args.extra_tags)

        if args.as_json:
            print(json.dumps(tagged, indent=2))
        else:
            if not tagged:
                print("No changes found.")
            for description, tags in tagged.items():
                print(f"{description}")
                print(f"  tags: {', '.join(tags)}")

        return 0
    except TaggerError as exc:
        print(f"[tagger error] {exc}")
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"[error] {exc}")
        return 2
