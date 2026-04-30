"""CLI sub-command for snapshot management."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schemashift.loader import load_schema_from_file, SchemaLoadError
from schemashift.snapshotter import (
    SnapshotError,
    take_snapshot,
    save_snapshot,
    load_snapshot,
    diff_snapshots,
    snapshot_metadata,
)
from schemashift.differ import is_breaking


def add_snapshot_subcommand(subparsers: argparse.Action) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "snapshot",
        help="Capture or compare schema snapshots",
    )
    sub = parser.add_subparsers(dest="snapshot_cmd", required=True)

    # snapshot capture
    capture = sub.add_parser("capture", help="Capture a new snapshot from a schema file")
    capture.add_argument("schema", help="Path to schema JSON file")
    capture.add_argument("output", help="Path to write the snapshot file")
    capture.add_argument("--label", default="", help="Optional human-readable label")

    # snapshot diff
    diff = sub.add_parser("diff", help="Diff two snapshot files")
    diff.add_argument("old", help="Path to the older snapshot")
    diff.add_argument("new", help="Path to the newer snapshot")

    # snapshot info
    info = sub.add_parser("info", help="Print metadata for a snapshot file")
    info.add_argument("snapshot", help="Path to snapshot file")


def run_snapshot(args: argparse.Namespace) -> int:
    cmd = args.snapshot_cmd

    if cmd == "capture":
        try:
            schema = load_schema_from_file(args.schema)
            snap = take_snapshot(schema, label=args.label)
            save_snapshot(snap, args.output)
            print(f"Snapshot saved to {args.output}")
            return 0
        except (SchemaLoadError, SnapshotError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

    if cmd == "diff":
        try:
            old = load_snapshot(args.old)
            new = load_snapshot(args.new)
            changes = diff_snapshots(old, new)
        except SnapshotError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

        if not changes:
            print("No schema changes detected.")
            return 0

        breaking = [c for c in changes if is_breaking(c)]
        for c in changes:
            tag = "[BREAKING]" if is_breaking(c) else "[non-breaking]"
            print(f"{tag} {c}")
        return 1 if breaking else 0

    if cmd == "info":
        try:
            snap = load_snapshot(args.snapshot)
            meta = snapshot_metadata(snap)
            print(json.dumps(meta, indent=2))
            return 0
        except SnapshotError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

    print(f"Unknown snapshot command: {cmd}", file=sys.stderr)
    return 2
