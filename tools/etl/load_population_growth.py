"""Load population growth observations into the POLITY warehouse."""

from tools.etl._common import load_world_bank_indicator


def main() -> int:
    count = load_world_bank_indicator("societal_indicators", "population_growth", "world_bank/population_growth/population_growth.json")
    print("Loaded {} population growth records.".format(count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
