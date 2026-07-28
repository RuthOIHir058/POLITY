"""Load World Bank country metadata into the master countries table."""

import sqlite3

from tools.etl._common import DATABASE_PATH, read_json


def main() -> int:
    payload = read_json("world_bank/countries.json")
    countries = payload[1]
    with sqlite3.connect(DATABASE_PATH) as connection:
        count = 0
        for country in countries:
            connection.execute(
                """
                INSERT INTO countries (iso3, country_name, region, income_group)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(iso3) DO UPDATE SET
                    country_name = excluded.country_name,
                    region = excluded.region,
                    income_group = excluded.income_group
                """,
                (
                    country["id"],
                    country["name"],
                    country["region"]["value"],
                    country["incomeLevel"]["value"],
                ),
            )
            count += 1
    print(f"Loaded {count} countries into SQLite.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
