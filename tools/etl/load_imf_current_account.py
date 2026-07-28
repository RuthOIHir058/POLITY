"""Load IMF current-account/GDP observations."""

import sqlite3

from tools.etl._common import DATABASE_PATH, read_json, upsert_rows


def main() -> int:
    payload = read_json("imf/current_account_gdp.json")
    indicator = next(iter(payload["values"]))
    values = payload["values"][indicator]
    rows = (
        (iso3, int(year), float(value))
        for iso3, years in values.items()
        for year, value in years.items()
        if value is not None
    )
    with sqlite3.connect(DATABASE_PATH) as connection:
        count = upsert_rows(connection, "economic_indicators", "current_account_gdp", rows)
    print(f"Loaded {count} current account records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
