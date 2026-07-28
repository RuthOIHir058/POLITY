"""Download the World Bank country metadata catalogue."""

from tools.download._common import download_file


def main() -> int:
    download_file(
        "https://api.worldbank.org/v2/country",
        "world_bank/countries.json",
        params={"format": "json", "per_page": 400},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
