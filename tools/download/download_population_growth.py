"""Download population growth observations from the World Bank API."""

from tools.download._common import download_world_bank_indicator


def main() -> int:
    download_world_bank_indicator("SP.POP.GROW", "world_bank/population_growth/population_growth.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
