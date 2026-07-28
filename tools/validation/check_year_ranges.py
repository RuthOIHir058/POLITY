"""Validate the published warehouse snapshot's table year ranges."""

from __future__ import annotations

import sqlite3

from tools.validation._common import database_parser, require_database

EXPECTED = {
    "economic_indicators": (1800, 2031),
    "governance_indicators": (1996, 2024),
    "societal_indicators": (1960, 2025),
}


def main(argv: list[str] | None = None) -> int:
    args = database_parser(__doc__).parse_args(argv)
    database = require_database(args.database)
    with sqlite3.connect(database) as connection:
        for table, expected in EXPECTED.items():
            actual = connection.execute(
                f"SELECT MIN(year), MAX(year) FROM {table}"
            ).fetchone()
            if tuple(actual) != expected:
                raise SystemExit(
                    f"FAIL: {table} year range expected {expected}, got {tuple(actual)}"
                )
            distinct = connection.execute(
                f"SELECT COUNT(DISTINCT year) FROM {table}"
            ).fetchone()[0]
            print(f"PASS {table:<24} {actual[0]}-{actual[1]} ({distinct} years)")
    print("YEAR RANGE VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
