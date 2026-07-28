"""Load GDP per capita observations into the POLITY warehouse."""

from tools.etl._common import load_world_bank_indicator


def main() -> int:
    count = load_world_bank_indicator("economic_indicators", "gdp_per_capita", "world_bank/gdp_per_capita/gdp_per_capita.json")
    print("Loaded {} GDP per capita records.".format(count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
