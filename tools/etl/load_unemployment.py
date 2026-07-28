"""Load unemployment observations into the POLITY warehouse."""

from tools.etl._common import load_world_bank_indicator


def main() -> int:
    count = load_world_bank_indicator("economic_indicators", "unemployment", "world_bank/unemployment/unemployment.json")
    print("Loaded {} unemployment records.".format(count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
