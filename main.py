"""Compatibility entry point for the POLITY command-line interface."""

from engine.cli import build_parser, main, policy_from_args, write_csv

__all__ = ["build_parser", "main", "policy_from_args", "write_csv"]


if __name__ == "__main__":
    raise SystemExit(main())
