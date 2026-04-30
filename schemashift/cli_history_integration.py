"""Standalone entry point for the history subcommand."""

from __future__ import annotations

import argparse
import sys

from schemashift.cli_history import add_history_subcommand, run_history


def build_standalone_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schemashift-history",
        description="Record and query schema diff history.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_history_subcommand(subparsers)
    return parser


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the history command into an existing subparser group."""
    add_history_subcommand(subparsers)


def main(argv: list[str] | None = None) -> int:
    parser = build_standalone_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
