"""Download life expectancy observations from the World Bank API."""

from tools.download._common import download_world_bank_indicator


def main() -> int:
    download_world_bank_indicator("SP.DYN.LE00.IN", "world_bank/life_expectancy/life_expectancy.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
