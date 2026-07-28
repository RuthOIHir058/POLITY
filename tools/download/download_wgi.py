"""Download World Governance Indicators series used by POLITY."""

from tools.download._common import download_file

SERIES = {
    "government_effectiveness": "GOV_WGI_GE.EST",
    "rule_of_law": "GOV_WGI_RL.EST",
    "political_stability": "GOV_WGI_PV.EST",
}


def main() -> int:
    for filename, series_code in SERIES.items():
        download_file(
            f"https://api.worldbank.org/v2/sources/3/country/all/series/{series_code}/data",
            f"wgi/{filename}.json",
            params={"format": "json", "per_page": 20000},
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
