"""Run the documented 2015-to-2024 historical calibration proxy.

This is not the guidebook's 2025 acceptance test. The bundled warehouse has no
country with all five required 2025 observations. The proxy uses 2024 and a
fixed expenditure split because category-level historical spending is absent.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import statistics
from dataclasses import dataclass
from pathlib import Path

from engine.core.helpers import clamp
from engine.core.initialize_country import initialize_country
from engine.core.policy_inputs import PolicyInputs
from engine.core.simulation_engine import SimulationEngine
from engine.data.country_loader import load_range, load_year
from tools.validation._common import database_parser, require_database

TARGETS = (
    "gdp_per_capita",
    "inflation",
    "unemployment",
    "debt_gdp",
    "life_expectancy",
)


@dataclass(frozen=True)
class ProxyResult:
    country_code: str
    predicted: dict[str, float]
    actual: dict[str, float]
    relative_error: dict[str, float]
    passed: dict[str, bool]

    @property
    def pass_count(self) -> int:
        return sum(self.passed.values())


def _average(rows: list[dict[str, object]], field: str) -> float | None:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return statistics.fmean(values) if values else None


def _relative_error(predicted: float, actual: float) -> float:
    return abs(predicted - actual) / max(abs(actual), 1e-12)


def _historical_policy(
    database: Path,
    country_code: str,
    start_year: int,
    fiscal_capacity: float,
) -> PolicyInputs | None:
    history = load_range(database, country_code, start_year - 5, start_year)
    revenue = _average(history, "revenue_gdp")
    expenditure = _average(history, "expenditure_gdp")
    inflation = _average(history, "inflation")
    if revenue is None or expenditure is None:
        return None

    # Revenue/expenditure warehouse values are percentages; PolicyInputs use ratios.
    tax_rate = clamp((revenue / 100.0) / fiscal_capacity, 0.05, 0.55)
    total_expenditure = clamp(expenditure / 100.0, 0.10, 0.65)
    inflation_target = clamp((inflation or 2.0) / 100.0, -0.05, 2.0)

    # Historical category shares are unavailable in the warehouse. This fixed,
    # explicitly documented split is a proxy rather than a fitted calibration.
    return PolicyInputs(
        tax_rate=tax_rate,
        total_expenditure_gdp=total_expenditure,
        health_share=0.15,
        education_share=0.20,
        infrastructure_share=0.20,
        social_transfers_share=0.20,
        admin_share=0.15,
        military_share=0.10,
        inflation_target=inflation_target,
        trade_policy=0.0,
    )


def run_proxy(database: Path, start_year: int, end_year: int) -> tuple[int, list[ProxyResult]]:
    with sqlite3.connect(database) as connection:
        codes = [row[0] for row in connection.execute("SELECT iso3 FROM countries ORDER BY iso3")]

    initialized = 0
    results: list[ProxyResult] = []
    for code in codes:
        try:
            state = initialize_country(code, start_year, database)
        except (LookupError, ValueError):
            continue
        initialized += 1

        policy = _historical_policy(database, code, start_year, state.fiscal_capacity)
        if policy is None:
            continue

        simulation = SimulationEngine.simulate(state, policy, end_year - start_year)
        if not simulation:
            continue
        final = simulation[-1]
        observed = load_year(database, code, end_year)
        actual_gdp_per_capita = observed.get("gdp_per_capita")
        if (
            actual_gdp_per_capita is None
            and observed.get("gdp_current_usd") is not None
            and observed.get("population") is not None
        ):
            actual_gdp_per_capita = float(observed["gdp_current_usd"]) / float(
                observed["population"]
            )

        actual_values: dict[str, float | None] = {
            "gdp_per_capita": (
                None if actual_gdp_per_capita is None else float(actual_gdp_per_capita)
            ),
            "inflation": (
                None
                if observed.get("inflation") is None
                else float(observed["inflation"]) / 100.0
            ),
            "unemployment": (
                None
                if observed.get("unemployment") is None
                else float(observed["unemployment"]) / 100.0
            ),
            "debt_gdp": (
                None
                if observed.get("debt_gdp") is None
                else float(observed["debt_gdp"]) / 100.0
            ),
            "life_expectancy": (
                None
                if observed.get("life_expectancy") is None
                else float(observed["life_expectancy"])
            ),
        }
        if any(value is None for value in actual_values.values()):
            continue

        predicted = {
            "gdp_per_capita": float(final.derived["gdp_per_capita"]),
            "inflation": final.state.inflation,
            "unemployment": final.state.unemployment,
            "debt_gdp": final.state.debt_gdp,
            "life_expectancy": final.state.life_expectancy,
        }
        actual = {name: float(actual_values[name]) for name in TARGETS}
        errors = {
            name: _relative_error(predicted[name], actual[name]) for name in TARGETS
        }
        passed = {name: error <= 0.20 for name, error in errors.items()}
        results.append(ProxyResult(code, predicted, actual, errors, passed))

    return initialized, results


def write_csv(path: Path, results: list[ProxyResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["country_code", "pass_count"]
    for target in TARGETS:
        fields.extend(
            [f"predicted_{target}", f"actual_{target}", f"relative_error_{target}", f"pass_{target}"]
        )
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for result in results:
            row: dict[str, object] = {
                "country_code": result.country_code,
                "pass_count": result.pass_count,
            }
            for target in TARGETS:
                row[f"predicted_{target}"] = result.predicted[target]
                row[f"actual_{target}"] = result.actual[target]
                row[f"relative_error_{target}"] = result.relative_error[target]
                row[f"pass_{target}"] = result.passed[target]
            writer.writerow(row)


def build_parser() -> argparse.ArgumentParser:
    parser = database_parser(__doc__)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument("--csv", type=Path, help="Optional detailed CSV output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    database = require_database(args.database)
    if args.end_year <= args.start_year:
        raise SystemExit("end-year must be greater than start-year")

    initialized, results = run_proxy(database, args.start_year, args.end_year)
    all_pass = [result for result in results if result.pass_count == len(TARGETS)]
    ranked = sorted(
        results,
        key=lambda result: (
            -result.pass_count,
            sum(result.relative_error.values()),
            result.country_code,
        ),
    )

    print(f"Initialized countries: {initialized}")
    print(f"Comparable countries: {len(results)}")
    print(f"Countries passing all five ±20% targets: {len(all_pass)}")
    print("Closest results:")
    for result in ranked[:10]:
        errors = ", ".join(
            f"{name}={result.relative_error[name]:.1%}" for name in TARGETS
        )
        print(f"  {result.country_code}: {result.pass_count}/5; {errors}")

    kenya = next((result for result in results if result.country_code == "KEN"), None)
    if kenya is not None:
        print("Kenya proxy:")
        for target in TARGETS:
            print(
                f"  {target}: predicted={kenya.predicted[target]:.8g}, "
                f"actual={kenya.actual[target]:.8g}, "
                f"error={kenya.relative_error[target]:.1%}, "
                f"pass={kenya.passed[target]}"
            )

    if args.csv:
        write_csv(args.csv, results)
        print(f"Detailed CSV: {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
