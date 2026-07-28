"""Load urban population observations into the POLITY warehouse."""

from tools.etl._common import load_world_bank_indicator


def main() -> int:
    count = load_world_bank_indicator("societal_indicators", "urban_population_pct", "world_bank/urban_population/urban_population.json")
    print("Loaded {} urban population records.".format(count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
