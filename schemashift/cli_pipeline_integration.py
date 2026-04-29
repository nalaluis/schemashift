"""Integration helper: wires the pipeline subcommand into the main CLI parser.

Usage (in cli.py or __main__.py)::

    from schemashift.cli_pipeline_integration import register
    register(subparsers)
"""

import argparse
import sys
from typing import Optional

from schemashift.cli_pipeline import add_pipeline_subcommand


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'pipeline' subcommand onto an existing subparsers group."""
    add_pipeline_subcommand(subparsers)


def build_standalone_parser() -> argparse.ArgumentParser:
    """Return a standalone argument parser with only the pipeline subcommand.

    Useful for testing or embedding.
    """
    parser = argparse.ArgumentParser(
        prog="schemashift-pipeline",
        description="Run the SchemaShift diff pipeline on two schema files.",
    )
    sub = parser.add_subparsers(dest="command")
    add_pipeline_subcommand(sub)
    return parser


def main(argv: Optional[list] = None) -> int:
    """Standalone entry point for the pipeline subcommand."""
    parser = build_standalone_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
