"""Download working-age share observations from the World Bank API."""

from tools.download._common import download_world_bank_indicator


def main() -> int:
    download_world_bank_indicator("SP.POP.1564.TO.ZS", "world_bank/working_age_share/working_age_share.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
