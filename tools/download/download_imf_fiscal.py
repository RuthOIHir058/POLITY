"""Download IMF DataMapper fiscal and current-account series."""

from tools.download._common import download_file

INDICATORS = {
    "GGXWDG_NGDP": "debt_gdp.json",
    "rev": "revenue_gdp.json",
    "exp": "expenditure_gdp.json",
    "BCA_NGDPD": "current_account_gdp.json",
}


def main() -> int:
    for indicator, filename in INDICATORS.items():
        download_file(
            f"https://www.imf.org/external/datamapper/api/v1/{indicator}",
            f"imf/{filename}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
