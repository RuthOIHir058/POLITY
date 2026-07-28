"""Shared paths and argument helpers for validation utilities."""

from __future__ import annotations

import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DATABASE = PROJECT_ROOT / "data" / "database" / "polity.db"
PACKAGED_DATABASE = PROJECT_ROOT / "engine" / "data" / "polity.db"
DEFAULT_DATABASE = (
    PROJECT_DATABASE if PROJECT_DATABASE.is_file() else PACKAGED_DATABASE
)


def database_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help="SQLite database; defaults to the bundled publication snapshot.",
    )
    return parser


def require_database(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Database not found: {resolved}")
    return resolved
