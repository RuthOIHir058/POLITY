"""Load inflation observations into the POLITY warehouse."""

from tools.etl._common import load_world_bank_indicator


def main() -> int:
    count = load_world_bank_indicator("economic_indicators", "inflation", "world_bank/inflation/inflation.json")
    print("Loaded {} inflation records.".format(count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
