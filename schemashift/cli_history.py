"""CLI subcommand for managing diff history."""

from __future__ import annotations

import argparse
import json
import sys

from schemashift.differ_history import HistoryError, load_history, query_history
from schemashift.loader import load_schema_from_file, SchemaLoadError
from schemashift.comparator import compare_schemas
from schemashift.differ_history import record_entry


def add_history_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("history", help="Manage diff history")
    sub = parser.add_subparsers(dest="history_cmd", required=True)

    rec = sub.add_parser("record", help="Record a diff into history")
    rec.add_argument("old", help="Old schema file")
    rec.add_argument("new", help="New schema file")
    rec.add_argument("--history-file", default=".schemashift_history.json")
    rec.add_argument("--label", default="", help="Optional label for this entry")

    show = sub.add_parser("show", help="Show history entries")
    show.add_argument("--history-file", default=".schemashift_history.json")
    show.add_argument("--label", default=None)
    show.add_argument("--breaking-only", action="store_true")

    parser.set_defaults(func=run_history)


def run_history(args: argparse.Namespace) -> int:
    if args.history_cmd == "record":
        return _run_record(args)
    if args.history_cmd == "show":
        return _run_show(args)
    return 1


def _run_record(args: argparse.Namespace) -> int:
    try:
        old = load_schema_from_file(args.old)
        new = load_schema_from_file(args.new)
    except SchemaLoadError as exc:
        print(f"Load error: {exc}", file=sys.stderr)
        return 2
    changes = compare_schemas(old, new)
    entry = record_entry(args.history_file, changes, label=args.label or None)
    print(f"Recorded {entry['change_count']} change(s) at {entry['recorded_at']}")
    return 0


def _run_show(args: argparse.Namespace) -> int:
    try:
        entries = query_history(
            args.history_file,
            label=args.label,
            breaking_only=args.breaking_only,
        )
    except HistoryError as exc:
        print(f"History error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(entries, indent=2))
    return 0
