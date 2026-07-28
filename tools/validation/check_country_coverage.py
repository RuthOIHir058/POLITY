"""Report country coverage and verify the Kenya publication smoke fixture."""

from __future__ import annotations

import sqlite3

from tools.validation._common import database_parser, require_database

TABLES = ("economic_indicators", "governance_indicators", "societal_indicators")


def main(argv: list[str] | None = None) -> int:
    args = database_parser(__doc__).parse_args(argv)
    database = require_database(args.database)
    with sqlite3.connect(database) as connection:
        countries = {row[0] for row in connection.execute("SELECT iso3 FROM countries")}
        print(f"countries table: {len(countries)} countries")
        if "KEN" not in countries:
            raise SystemExit("FAIL: KEN missing from countries table")

        for table in TABLES:
            table_countries = {
                row[0]
                for row in connection.execute(f"SELECT DISTINCT iso3 FROM {table}")
            }
            print(f"{table:<24} {len(table_countries)} countries")
            print(f"  missing_vs_master: {len(countries - table_countries)}")

        for table in TABLES:
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE iso3 = ? AND year = ?",
                ("KEN", 2023),
            ).fetchone()[0]
            if count != 1:
                raise SystemExit(f"FAIL: KEN 2023 missing from {table}")
            print(f"PASS KEN 2023 {table}")

    print("COUNTRY COVERAGE VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
