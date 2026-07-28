"""Load exports/imports shares and derive trade openness as their sum."""

import sqlite3

from tools.etl._common import DATABASE_PATH, load_world_bank_indicator


def main() -> int:
    exports = load_world_bank_indicator(
        "economic_indicators", "exports_gdp", "world_bank/exports_gdp/exports_gdp.json"
    )
    imports = load_world_bank_indicator(
        "economic_indicators", "imports_gdp", "world_bank/imports_gdp/imports_gdp.json"
    )
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            UPDATE economic_indicators
            SET trade_openness = COALESCE(exports_gdp, 0) + COALESCE(imports_gdp, 0)
            WHERE exports_gdp IS NOT NULL OR imports_gdp IS NOT NULL
            """
        )
    print(f"exports_gdp: {exports}")
    print(f"imports_gdp: {imports}")
    print("trade openness complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
