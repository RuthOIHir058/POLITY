"""Download urban population observations from the World Bank API."""

from tools.download._common import download_world_bank_indicator


def main() -> int:
    download_world_bank_indicator("SP.URB.TOTL.IN.ZS", "world_bank/urban_population/urban_population.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
