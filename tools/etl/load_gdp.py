"""Load GDP observations into the POLITY warehouse."""

from tools.etl._common import load_world_bank_indicator


def main() -> int:
    count = load_world_bank_indicator("economic_indicators", "gdp_current_usd", "world_bank/gdp/gdp_current_usd.json")
    print("Loaded {} GDP records.".format(count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
