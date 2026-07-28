"""Validate the published SQLite warehouse schema and primary keys."""

from __future__ import annotations

import sqlite3

from tools.validation._common import database_parser, require_database

EXPECTED = {
    "countries": {
        "columns": [
            ("iso3", "TEXT"),
            ("country_name", "TEXT"),
            ("region", "TEXT"),
            ("income_group", "TEXT"),
        ],
        "pk": ["iso3"],
    },
    "economic_indicators": {
        "columns": [
            ("iso3", "TEXT"),
            ("year", "INTEGER"),
            ("gdp_current_usd", "REAL"),
            ("gdp_per_capita", "REAL"),
            ("inflation", "REAL"),
            ("debt_gdp", "REAL"),
            ("revenue_gdp", "REAL"),
            ("expenditure_gdp", "REAL"),
            ("unemployment", "REAL"),
            ("current_account_gdp", "REAL"),
            ("exports_gdp", "REAL"),
            ("imports_gdp", "REAL"),
            ("trade_openness", "REAL"),
        ],
        "pk": ["iso3", "year"],
    },
    "governance_indicators": {
        "columns": [
            ("iso3", "TEXT"),
            ("year", "INTEGER"),
            ("government_effectiveness", "REAL"),
            ("rule_of_law", "REAL"),
            ("corruption_index", "REAL"),
            ("political_stability", "REAL"),
        ],
        "pk": ["iso3", "year"],
    },
    "societal_indicators": {
        "columns": [
            ("iso3", "TEXT"),
            ("year", "INTEGER"),
            ("life_expectancy", "REAL"),
            ("gini", "REAL"),
            ("population", "REAL"),
            ("population_growth", "REAL"),
            ("urban_population_pct", "REAL"),
            ("youth_share", "REAL"),
            ("working_age_share", "REAL"),
            ("elderly_share", "REAL"),
            ("hdi", "REAL"),
            ("expected_years_schooling", "REAL"),
            ("mean_years_schooling", "REAL"),
            ("school_life_expectancy", "REAL"),
        ],
        "pk": ["iso3", "year"],
    },
}


def main(argv: list[str] | None = None) -> int:
    args = database_parser(__doc__).parse_args(argv)
    database = require_database(args.database)
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise SystemExit(f"FAIL: SQLite integrity_check returned: {integrity}")
        foreign_key_issues = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_issues:
            raise SystemExit(
                f"FAIL: SQLite foreign_key_check found {len(foreign_key_issues)} issue(s)"
            )
        print("PASS SQLite integrity_check and foreign_key_check")

        existing = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        for table, expected in EXPECTED.items():
            if table not in existing:
                raise SystemExit(f"FAIL: missing table: {table}")
            info = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
            actual_columns = [(row[1], row[2]) for row in info]
            if actual_columns != expected["columns"]:
                raise SystemExit(
                    f"FAIL: column mismatch in {table}\n"
                    f"Expected: {expected['columns']}\nActual:   {actual_columns}"
                )
            actual_pk = [row[1] for row in sorted(info, key=lambda row: row[5]) if row[5]]
            if actual_pk != expected["pk"]:
                raise SystemExit(
                    f"FAIL: primary-key mismatch in {table}: "
                    f"expected {expected['pk']}, got {actual_pk}"
                )
            count = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            if count == 0:
                raise SystemExit(f"FAIL: empty table: {table}")
            print(f"PASS {table:<24} rows={count}")
    print("SCHEMA VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
