"""Load World Governance Indicators from the downloaded API payloads."""

import sqlite3

from tools.etl._common import DATABASE_PATH, read_json, upsert_rows

FILES = {
    "government_effectiveness": "wgi/government_effectiveness.json",
    "rule_of_law": "wgi/rule_of_law.json",
    "political_stability": "wgi/political_stability.json",
}


def main() -> int:
    with sqlite3.connect(DATABASE_PATH) as connection:
        for column, source in FILES.items():
            records = read_json(source)["source"]["data"]
            rows = []
            for record in records:
                if record.get("value") is None:
                    continue
                variables = record["variable"]
                rows.append(
                    (
                        variables[0]["id"],
                        int(variables[2]["value"]),
                        float(record["value"]),
                    )
                )
            count = upsert_rows(connection, "governance_indicators", column, rows)
            print(f"{column}: {count}")
    print("WGI load complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
