"""Download GDP observations from the World Bank API."""

from tools.download._common import download_world_bank_indicator


def main() -> int:
    download_world_bank_indicator("NY.GDP.MKTP.CD", "world_bank/gdp/gdp_current_usd.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
