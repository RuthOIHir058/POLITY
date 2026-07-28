"""Download school life expectancy observations from the World Bank API."""

from tools.download._common import download_world_bank_indicator


def main() -> int:
    download_world_bank_indicator("SE.SCH.LIFE", "world_bank/school_life_expectancy/school_life_expectancy.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
