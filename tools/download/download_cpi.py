"""Download Transparency International's CPI 2024 workbook."""

from tools.download._common import download_file


def main() -> int:
    download_file(
        "https://images.transparencycdn.org/images/CPI2024-Results-and-trends.xlsx",
        "cpi/cpi_2024.xlsx",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
