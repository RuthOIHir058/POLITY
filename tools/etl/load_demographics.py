"""Load youth, working-age, and elderly population shares."""

from tools.etl._common import load_world_bank_indicator

INDICATORS = {
    "youth_share": "world_bank/youth_share/youth_share.json",
    "working_age_share": "world_bank/working_age_share/working_age_share.json",
    "elderly_share": "world_bank/elderly_share/elderly_share.json",
}


def main() -> int:
    total = 0
    for column, source in INDICATORS.items():
        count = load_world_bank_indicator("societal_indicators", column, source)
        print(f"{column}: {count}")
        total += count
    print(f"Total loaded: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
