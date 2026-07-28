"""Validate that the warehouse adapter returns the canonical CountryState contract."""

from __future__ import annotations

from dataclasses import fields

from engine.core.country_state import CountryState
from engine.data.country_loader import load_country
from tools.validation._common import database_parser, require_database


def main(argv: list[str] | None = None) -> int:
    parser = database_parser(__doc__)
    parser.add_argument("--country", default="KEN", help="ISO3 country code")
    parser.add_argument("--year", type=int, default=2023)
    args = parser.parse_args(argv)
    database = require_database(args.database)

    state = load_country(args.country, args.year, db_conn=database)
    expected_fields = {item.name for item in fields(CountryState)}
    actual_fields = set(vars(state))
    missing = sorted(expected_fields - actual_fields)
    extra = sorted(actual_fields - expected_fields)
    if missing or extra:
        raise SystemExit(
            f"FAIL: CountryState mismatch; missing={missing}, extra={extra}"
        )

    required = {
        "country_code": state.country_code,
        "year": state.year,
        "gdp": state.gdp,
        "population": state.population,
        "inflation": state.inflation,
        "debt_gdp": state.debt_gdp,
        "human_capital": state.human_capital,
        "conflict_risk": state.conflict_risk,
    }
    for name, value in required.items():
        if value is None:
            raise SystemExit(f"FAIL: required state field is None: {name}")
        print(f"PASS {name:<20} {value}")

    state.validate_ranges()
    print(f"CountryState field count: {len(expected_fields)}")
    print("LOADER CONTRACT VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
