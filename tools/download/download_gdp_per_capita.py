"""Download GDP per capita observations from the World Bank API."""

from tools.download._common import download_world_bank_indicator


def main() -> int:
    download_world_bank_indicator("NY.GDP.PCAP.CD", "world_bank/gdp_per_capita/gdp_per_capita.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
