"""Download youth share observations from the World Bank API."""

from tools.download._common import download_world_bank_indicator


def main() -> int:
    download_world_bank_indicator("SP.POP.0014.TO.ZS", "world_bank/youth_share/youth_share.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
