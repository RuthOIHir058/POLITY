"""Download inflation observations from the World Bank API."""

from tools.download._common import download_world_bank_indicator


def main() -> int:
    download_world_bank_indicator("FP.CPI.TOTL.ZG", "world_bank/inflation/inflation.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
