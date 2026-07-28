"""Print null-rate diagnostics for every warehouse indicator column."""

from __future__ import annotations

import sqlite3

from tools.validation._common import database_parser, require_database

TABLES = ("economic_indicators", "governance_indicators", "societal_indicators")


def main(argv: list[str] | None = None) -> int:
    args = database_parser(__doc__).parse_args(argv)
    database = require_database(args.database)
    with sqlite3.connect(database) as connection:
        for table in TABLES:
            print(f"\n{'=' * 70}\n{table}\n{'=' * 70}")
            total = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            info = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
            results = []
            for row in info:
                column = row[1]
                nulls = connection.execute(
                    f'SELECT COUNT(*) FROM "{table}" WHERE "{column}" IS NULL'
                ).fetchone()[0]
                rate = nulls / total * 100.0 if total else 0.0
                results.append((column, nulls, rate))
            for column, nulls, rate in sorted(results, key=lambda item: item[2], reverse=True):
                print(f"{column:<28}{nulls:>8} ({rate:6.2f}%)")
    print("\nMISSING DATA AUDIT COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
