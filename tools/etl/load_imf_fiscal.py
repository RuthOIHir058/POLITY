"""Load IMF debt, revenue, and expenditure ratios."""

import sqlite3

from tools.etl._common import DATABASE_PATH, read_json, upsert_rows

FILES = {
    "imf/debt_gdp.json": ("GGXWDG_NGDP", "debt_gdp"),
    "imf/revenue_gdp.json": ("rev", "revenue_gdp"),
    "imf/expenditure_gdp.json": ("exp", "expenditure_gdp"),
}


def main() -> int:
    total = 0
    with sqlite3.connect(DATABASE_PATH) as connection:
        for source, (indicator, column) in FILES.items():
            values = read_json(source)["values"][indicator]
            rows = (
                (iso3, int(year), float(value))
                for iso3, years in values.items()
                for year, value in years.items()
                if value is not None
            )
            count = upsert_rows(connection, "economic_indicators", column, rows)
            print(f"{column}: {count}")
            total += count
    print(f"Total loaded: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
