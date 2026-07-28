"""Download the UNDP 2025 Human Development Report statistical annex."""

from tools.download._common import download_file


def main() -> int:
    download_file(
        "https://hdr.undp.org/sites/default/files/2025_HDR/HDR25_Statistical_Annex_HDI_Table.xlsx",
        "undp/hdi_2025.xlsx",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
