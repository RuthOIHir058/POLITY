"""Compare two deterministic policy paths from the same initial state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.core.initialize_country import initialize_country  # noqa: E402
from engine.core.simulation_engine import SimulationEngine  # noqa: E402
from engine.data.country_loader import DEFAULT_DB_PATH  # noqa: E402
from examples.run_custom_policy import load_policy  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", default="KEN")
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--years", type=int, default=20)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=PROJECT_ROOT / "configs" / "baseline_policy.json",
    )
    parser.add_argument(
        "--alternative",
        type=Path,
        default=PROJECT_ROOT
        / "configs"
        / "education_infrastructure_reform.json",
    )
    parser.add_argument("--database", type=Path, default=DEFAULT_DB_PATH)
    return parser


def final_metrics(result) -> tuple[float, float, float, float, float]:
    return (
        result.derived["gdp_per_capita"],
        result.state.inflation,
        result.state.unemployment,
        result.state.debt_gdp,
        result.reference["hdi"],
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    state = initialize_country(args.country, args.start_year, args.database)
    baseline = SimulationEngine.simulate(
        state, load_policy(args.baseline), args.years
    )
    alternative = SimulationEngine.simulate(
        state, load_policy(args.alternative), args.years
    )
    if not baseline or not alternative:
        print("No years requested; nothing to compare.")
        return 0

    headings = ("scenario", "gdp_pc", "inflation", "unemployment", "debt_gdp", "hdi")
    print("  ".join(f"{item:>14}" for item in headings))
    for name, result in (("baseline", baseline[-1]), ("alternative", alternative[-1])):
        gdp_pc, inflation, unemployment, debt_gdp, hdi = final_metrics(result)
        print(
            f"{name:>14}  {gdp_pc:14.2f}  {inflation:14.2%}  "
            f"{unemployment:14.2%}  {debt_gdp:14.2%}  {hdi:14.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
