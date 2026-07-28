"""Create the current POLITY SQLite warehouse schema without deleting data."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "database" / "polity.db"
SCHEMA_PATH = PROJECT_ROOT / "docs" / "data" / "schema_reference.sql"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.database.parent.mkdir(parents=True, exist_ok=True)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with sqlite3.connect(args.database) as connection:
        connection.executescript(schema)
    print(f"Schema ready: {args.database.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
