"""Download exports/GDP observations from the World Bank API."""

from tools.download._common import download_world_bank_indicator


def main() -> int:
    download_world_bank_indicator("NE.EXP.GNFS.ZS", "world_bank/exports_gdp/exports_gdp.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
