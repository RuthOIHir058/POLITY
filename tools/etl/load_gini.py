"""Load Gini observations into the POLITY warehouse."""

from tools.etl._common import load_world_bank_indicator


def main() -> int:
    count = load_world_bank_indicator("societal_indicators", "gini", "world_bank/gini/gini.json")
    print("Loaded {} Gini records.".format(count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
