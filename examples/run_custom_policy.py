"""Run a POLITY simulation from a JSON policy file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.core.initialize_country import initialize_country  # noqa: E402
from engine.core.policy_inputs import PolicyInputs  # noqa: E402
from engine.core.simulation_engine import SimulationEngine  # noqa: E402
from engine.data.country_loader import DEFAULT_DB_PATH  # noqa: E402
from engine.cli import write_csv  # noqa: E402


def load_policy(path: Path) -> PolicyInputs:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Policy JSON must contain one object")
    return PolicyInputs(**payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", default="KEN", help="ISO3 country code")
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--years", type=int, default=20)
    parser.add_argument(
        "--policy",
        type=Path,
        default=PROJECT_ROOT / "configs" / "baseline_policy.json",
    )
    parser.add_argument("--database", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "results" / "custom_policy.csv",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        policy = load_policy(args.policy)
        state = initialize_country(args.country, args.start_year, args.database)
        results = SimulationEngine.simulate(state, policy, args.years)
    except (FileNotFoundError, LookupError, TypeError, ValueError) as exc:
        parser.error(str(exc))

    write_csv(results, args.output)
    final = results[-1] if results else None
    print(f"Policy: {args.policy}")
    print(f"Output: {args.output}")
    if final is not None:
        print(
            f"Final year {final.state.year}: "
            f"GDP per capita={final.derived['gdp_per_capita']:.2f}, "
            f"inflation={final.state.inflation:.2%}, "
            f"debt/GDP={final.state.debt_gdp:.2%}, "
            f"HDI={final.reference['hdi']:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
