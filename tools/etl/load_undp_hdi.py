"""Load 2023 HDI and schooling indicators from the UNDP 2025 workbook."""

from __future__ import annotations

import sqlite3

import pandas as pd

from tools.etl._common import DATABASE_PATH, read_json, raw_path

DATA_YEAR = 2023

AGGREGATE_LABELS = {
    "Arab States",
    "Developing countries",
    "East Asia and the Pacific",
    "Europe and Central Asia",
    "High human development",
    "Latin America and the Caribbean",
    "Least developed countries",
    "Low human development",
    "Medium human development",
    "Organisation for Economic Co-operation and Development",
    "Small island developing states",
    "Very high human development",
}

NAME_OVERRIDES = {
    "Hong Kong, China (SAR)": "HKG",
    "Bahamas": "BHS",
    "Bolivia (Plurinational State of)": "BOL",
    "Congo": "COG",
    "Congo (Democratic Republic of the)": "COD",
    "Côte d'Ivoire": "CIV",
    "Egypt": "EGY",
    "Eswatini (Kingdom of)": "SWZ",
    "Gambia": "GMB",
    "Iran (Islamic Republic of)": "IRN",
    "Korea (Republic of)": "KOR",
    "Kyrgyzstan": "KGZ",
    "Lao People's Democratic Republic": "LAO",
    "Micronesia (Federated States of)": "FSM",
    "Moldova (Republic of)": "MDA",
    "Palestine, State of": "PSE",
    "Saint Kitts and Nevis": "KNA",
    "Saint Lucia": "LCA",
    "Saint Vincent and the Grenadines": "VCT",
    "Slovakia": "SVK",
    "Somalia": "SOM",
    "Tanzania (United Republic of)": "TZA",
    "Türkiye": "TUR",
    "Venezuela (Bolivarian Republic of)": "VEN",
    "Yemen": "YEM",
}


def main() -> int:
    countries = read_json("world_bank/countries.json")[1]
    name_to_iso3 = {row["name"].strip(): row["id"] for row in countries}
    name_to_iso3.update(NAME_OVERRIDES)

    frame = pd.read_excel(
        raw_path("undp/hdi_2025.xlsx"), sheet_name="Table 1. HDI", header=None
    ).iloc[8:]
    invalid = {"..", "...", ""}
    loaded = 0
    missing: set[str] = set()
    with sqlite3.connect(DATABASE_PATH) as connection:
        for _, row in frame.iterrows():
            country = str(row[1]).strip()
            hdi, expected_school, mean_school = row[2], row[6], row[8]
            if pd.isna(hdi) or str(hdi).strip() in invalid:
                continue
            if country in AGGREGATE_LABELS:
                continue
            iso3 = name_to_iso3.get(country)
            if not iso3:
                missing.add(country)
                continue
            expected = (
                None
                if pd.isna(expected_school) or str(expected_school).strip() in invalid
                else float(expected_school)
            )
            mean = (
                None
                if pd.isna(mean_school) or str(mean_school).strip() in invalid
                else float(mean_school)
            )
            connection.execute(
                """
                INSERT INTO societal_indicators (
                    iso3, year, hdi, expected_years_schooling, mean_years_schooling
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(iso3, year) DO UPDATE SET
                    hdi = excluded.hdi,
                    expected_years_schooling = excluded.expected_years_schooling,
                    mean_years_schooling = excluded.mean_years_schooling
                """,
                (iso3, DATA_YEAR, float(hdi), expected, mean),
            )
            loaded += 1

    print(f"Loaded: {loaded}")
    if missing:
        print("Missing mappings:")
        for name in sorted(missing):
            print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
