"""Load life expectancy observations into the POLITY warehouse."""

from tools.etl._common import load_world_bank_indicator


def main() -> int:
    count = load_world_bank_indicator("societal_indicators", "life_expectancy", "world_bank/life_expectancy/life_expectancy.json")
    print("Loaded {} life expectancy records.".format(count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
