"""Shared paths and safe upsert helpers for the POLITY warehouse."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = Path(
    os.environ.get("POLITY_DATABASE", PROJECT_ROOT / "data" / "database" / "polity.db")
).expanduser().resolve()
RAW_DATA_ROOT = Path(
    os.environ.get("POLITY_RAW_DATA", PROJECT_ROOT / "data" / "raw")
).expanduser().resolve()

ALLOWED_COLUMNS = {
    "economic_indicators": {
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
    },
    "governance_indicators": {
        "government_effectiveness",
        "rule_of_law",
        "corruption_index",
        "political_stability",
    },
    "societal_indicators": {
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
    },
}


def raw_path(relative: str) -> Path:
    return RAW_DATA_ROOT / relative


def read_json(relative: str):
    return json.loads(raw_path(relative).read_text(encoding="utf-8"))


def world_bank_records(relative: str) -> list[dict]:
    payload = read_json(relative)
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        raise ValueError(f"Unexpected World Bank payload in {relative}")
    return payload[1]


def _validate_destination(table: str, column: str) -> None:
    if table not in ALLOWED_COLUMNS or column not in ALLOWED_COLUMNS[table]:
        raise ValueError(f"Unsupported warehouse destination: {table}.{column}")


def upsert_rows(
    connection: sqlite3.Connection,
    table: str,
    column: str,
    rows: Iterable[tuple[str, int, float]],
) -> int:
    """Upsert allowlisted indicator rows without replacing unrelated columns."""

    _validate_destination(table, column)
    sql = f"""
        INSERT INTO {table} (iso3, year, {column})
        VALUES (?, ?, ?)
        ON CONFLICT(iso3, year)
        DO UPDATE SET {column} = excluded.{column}
    """
    count = 0
    for iso3, year, value in rows:
        if not iso3:
            continue
        connection.execute(sql, (iso3, int(year), float(value)))
        count += 1
    return count


def load_world_bank_indicator(table: str, column: str, relative: str) -> int:
    records = world_bank_records(relative)
    rows = (
        (row.get("countryiso3code", ""), int(row["date"]), float(row["value"]))
        for row in records
        if row.get("countryiso3code") and row.get("value") is not None
    )
    with sqlite3.connect(DATABASE_PATH) as connection:
        return upsert_rows(connection, table, column, rows)
