"""SQLite warehouse adapter for POLITY country initialization.

This module returns raw historical values in warehouse units. Conversion to the
canonical simulation state occurs only in ``engine.core.initialize_country``.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from engine.core.country_state import CountryState

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DB_PATH = PROJECT_ROOT / "data" / "database" / "polity.db"
PACKAGED_DB_PATH = Path(__file__).resolve().with_name("polity.db")
DEFAULT_DB_PATH = (
    PROJECT_DB_PATH if PROJECT_DB_PATH.exists() else PACKAGED_DB_PATH
)
DB_PATH = DEFAULT_DB_PATH  # Backward-compatible public name.

ECONOMIC_FIELDS = (
    "gdp_current_usd",
    "gdp_per_capita",
    "inflation",
    "debt_gdp",
    "revenue_gdp",
    "expenditure_gdp",
    "unemployment",
    "current_account_gdp",
    "exports_gdp",
    "imports_gdp",
    "trade_openness",
)
GOVERNANCE_FIELDS = (
    "government_effectiveness",
    "rule_of_law",
    "corruption_index",
    "political_stability",
)
SOCIETAL_FIELDS = (
    "life_expectancy",
    "gini",
    "population",
    "population_growth",
    "urban_population_pct",
    "youth_share",
    "working_age_share",
    "elderly_share",
    "hdi",
    "expected_years_schooling",
    "mean_years_schooling",
    "school_life_expectancy",
)
TABLE_FIELDS = {
    "economic_indicators": ECONOMIC_FIELDS,
    "governance_indicators": GOVERNANCE_FIELDS,
    "societal_indicators": SOCIETAL_FIELDS,
}

ConnectionInput = sqlite3.Connection | str | Path | None


@contextmanager
def connection_scope(db_conn: ConnectionInput = None) -> Iterator[sqlite3.Connection]:
    """Yield a row-enabled SQLite connection and close only owned connections."""

    if isinstance(db_conn, sqlite3.Connection):
        previous_factory = db_conn.row_factory
        db_conn.row_factory = sqlite3.Row
        try:
            yield db_conn
        finally:
            db_conn.row_factory = previous_factory
        return

    path = Path(db_conn) if db_conn is not None else DEFAULT_DB_PATH
    if not path.exists():
        raise FileNotFoundError(f"POLITY database not found: {path}")
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def load_country_metadata(
    db_conn: ConnectionInput,
    country_code: str,
) -> dict[str, object]:
    code = country_code.upper()
    with connection_scope(db_conn) as connection:
        row = connection.execute(
            """
            SELECT iso3, country_name, region, income_group
            FROM countries
            WHERE iso3 = ?
            """,
            (code,),
        ).fetchone()
    if row is None:
        raise LookupError(f"Unknown country code: {code}")
    return dict(row)


def load_year(
    db_conn: ConnectionInput,
    country_code: str,
    year: int,
) -> dict[str, object]:
    """Load one raw baseline year, retaining ``None`` for missing indicators."""

    code = country_code.upper()
    with connection_scope(db_conn) as connection:
        metadata = connection.execute(
            """
            SELECT iso3, country_name, region, income_group
            FROM countries
            WHERE iso3 = ?
            """,
            (code,),
        ).fetchone()
        if metadata is None:
            raise LookupError(f"Unknown country code: {code}")

        result: dict[str, object] = {
            "country_code": code,
            "iso3": code,
            "country_name": metadata["country_name"],
            "region": metadata["region"],
            "income_group": metadata["income_group"],
            "year": int(year),
        }
        for fields in TABLE_FIELDS.values():
            result.update({field: None for field in fields})

        for table, fields in TABLE_FIELDS.items():
            columns = ", ".join(fields)
            row = connection.execute(
                f"SELECT {columns} FROM {table} WHERE iso3 = ? AND year = ?",
                (code, int(year)),
            ).fetchone()
            if row is not None:
                result.update({field: row[field] for field in fields})

    return result


def load_range(
    db_conn: ConnectionInput,
    country_code: str,
    start_year: int,
    end_year: int,
) -> list[dict[str, object]]:
    """Load raw annual rows from ``start_year`` through ``end_year`` inclusive."""

    if end_year < start_year:
        return []
    code = country_code.upper()
    with connection_scope(db_conn) as connection:
        # Validate country once and reuse the same connection for all years.
        metadata = connection.execute(
            "SELECT country_name, region, income_group FROM countries WHERE iso3 = ?",
            (code,),
        ).fetchone()
        if metadata is None:
            raise LookupError(f"Unknown country code: {code}")

        rows_by_year: dict[int, dict[str, object]] = {}
        for table, fields in TABLE_FIELDS.items():
            columns = ", ".join(("year",) + fields)
            for row in connection.execute(
                f"""
                SELECT {columns}
                FROM {table}
                WHERE iso3 = ? AND year BETWEEN ? AND ?
                ORDER BY year
                """,
                (code, int(start_year), int(end_year)),
            ):
                year = int(row["year"])
                merged = rows_by_year.setdefault(
                    year,
                    {
                        "country_code": code,
                        "iso3": code,
                        "country_name": metadata["country_name"],
                        "region": metadata["region"],
                        "income_group": metadata["income_group"],
                        "year": year,
                    },
                )
                merged.update({field: row[field] for field in fields})

        for merged in rows_by_year.values():
            for fields in TABLE_FIELDS.values():
                for field in fields:
                    merged.setdefault(field, None)

    return [rows_by_year[year] for year in sorted(rows_by_year)]


def load_nearest_value(
    db_conn: ConnectionInput,
    country_code: str,
    table: str,
    column: str,
    year: int,
) -> float | None:
    """Load the nearest non-null same-country observation.

    Equidistant observations prefer the earlier year to avoid future leakage
    whenever a historical value is available.
    """

    if table not in TABLE_FIELDS or column not in TABLE_FIELDS[table]:
        raise ValueError(f"Unsupported warehouse field: {table}.{column}")

    code = country_code.upper()
    with connection_scope(db_conn) as connection:
        row = connection.execute(
            f"""
            SELECT {column}, year
            FROM {table}
            WHERE iso3 = ? AND {column} IS NOT NULL
            ORDER BY ABS(year - ?), CASE WHEN year <= ? THEN 0 ELSE 1 END, year DESC
            LIMIT 1
            """,
            (code, int(year), int(year)),
        ).fetchone()
    return None if row is None else float(row[column])


def load_country(
    iso3: str,
    year: int,
    db_conn: ConnectionInput = None,
    historical_window: int = 5,
) -> CountryState:
    """Compatibility convenience: return an initialized canonical state."""

    from engine.core.initialize_country import initialize_country

    return initialize_country(
        iso3,
        year,
        db_conn=db_conn,
        historical_window=historical_window,
    )
