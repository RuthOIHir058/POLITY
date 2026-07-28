"""Download Gini observations from the World Bank API."""

from tools.download._common import download_world_bank_indicator


def main() -> int:
    download_world_bank_indicator("SI.POV.GINI", "world_bank/gini/gini.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
