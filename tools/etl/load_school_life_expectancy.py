"""Load school life expectancy observations into the POLITY warehouse."""

from tools.etl._common import load_world_bank_indicator


def main() -> int:
    count = load_world_bank_indicator("societal_indicators", "school_life_expectancy", "world_bank/school_life_expectancy/school_life_expectancy.json")
    print("Loaded {} school life expectancy records.".format(count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
