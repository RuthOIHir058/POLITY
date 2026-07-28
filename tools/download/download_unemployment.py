"""Download unemployment observations from the World Bank API."""

from tools.download._common import download_world_bank_indicator


def main() -> int:
    download_world_bank_indicator("SL.UEM.TOTL.ZS", "world_bank/unemployment/unemployment.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
