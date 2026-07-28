"""Command-line interface for the deterministic POLITY V1 engine."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any

from engine import __version__
from engine.core.initialize_country import initialize_country
from engine.core.policy_inputs import PolicyInputs
from engine.core.simulation_engine import SimulationEngine
from engine.data.country_loader import DEFAULT_DB_PATH


DEFAULT_POLICY = PolicyInputs(
    tax_rate=0.40,
    total_expenditure_gdp=0.24,
    health_share=0.15,
    education_share=0.20,
    infrastructure_share=0.20,
    social_transfers_share=0.20,
    admin_share=0.15,
    military_share=0.10,
    inflation_target=0.02,
    trade_policy=0.0,
)

_POLICY_FIELDS = {item.name for item in fields(PolicyInputs)}


def _optional_float(parser: argparse.ArgumentParser, name: str, help_text: str) -> None:
    parser.add_argument(name, type=float, default=None, help=help_text)


def build_parser() -> argparse.ArgumentParser:
    """Build the public CLI parser."""

    parser = argparse.ArgumentParser(
        prog="polity",
        description="Run a deterministic POLITY V1 country simulation.",
    )
    parser.add_argument("country", nargs="?", default="KEN", help="ISO3 code")
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--years", type=int, default=20)
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="SQLite warehouse; defaults to the bundled publication database.",
    )
    parser.add_argument(
        "--policy-file",
        type=Path,
        help="JSON object containing PolicyInputs fields; CLI overrides win.",
    )

    _optional_float(parser, "--tax-rate", "Target tax revenue as a GDP fraction.")
    _optional_float(parser, "--expenditure", "Total expenditure as a GDP fraction.")
    _optional_float(parser, "--health-share", "Share of expenditure allocated to health.")
    _optional_float(
        parser, "--education-share", "Share of expenditure allocated to education."
    )
    _optional_float(
        parser,
        "--infrastructure-share",
        "Share of expenditure allocated to infrastructure.",
    )
    _optional_float(
        parser,
        "--social-transfers-share",
        "Share of expenditure allocated to social transfers.",
    )
    _optional_float(parser, "--admin-share", "Share allocated to administration.")
    _optional_float(parser, "--military-share", "Share allocated to military.")
    _optional_float(parser, "--inflation-target", "Central-bank inflation target.")
    _optional_float(parser, "--trade-policy", "Structural trade policy in [-1, 1].")

    parser.add_argument(
        "--output",
        type=Path,
        help="Optional CSV path for the annual summary.",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Print notable/significant/critical audit entries after each year.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"POLITY Engine {__version__}",
    )
    return parser


def load_policy_file(path: Path) -> PolicyInputs:
    """Load a policy JSON file, rejecting unknown keys and non-numeric values."""

    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Cannot read policy file {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in policy file {path} at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError("Policy file must contain one JSON object")

    unknown = sorted(set(payload) - _POLICY_FIELDS)
    if unknown:
        raise ValueError(f"Unknown policy fields: {', '.join(unknown)}")

    values = asdict(DEFAULT_POLICY)
    for key, value in payload.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Policy field {key} must be numeric")
        values[key] = float(value)
    return PolicyInputs(**values)


def policy_from_args(args: argparse.Namespace) -> PolicyInputs:
    """Build the effective policy from defaults, a JSON file, and CLI overrides."""

    policy_file = getattr(args, "policy_file", None)
    policy = load_policy_file(policy_file) if policy_file else DEFAULT_POLICY
    overrides = {
        "tax_rate": args.tax_rate,
        "total_expenditure_gdp": args.expenditure,
        "health_share": args.health_share,
        "education_share": args.education_share,
        "infrastructure_share": args.infrastructure_share,
        "social_transfers_share": args.social_transfers_share,
        "admin_share": args.admin_share,
        "military_share": args.military_share,
        "inflation_target": args.inflation_target,
        "trade_policy": args.trade_policy,
    }
    supplied = {name: value for name, value in overrides.items() if value is not None}
    return policy.with_updates(**supplied) if supplied else policy


def _print_results(country_code: str, start_year: int, results: list, audit: bool) -> None:
    print(
        f"POLITY V1 | {country_code} | start {start_year} | "
        f"{len(results)} deterministic years"
    )
    print(
        "year  growth   gdp_pc    inflation  unemployment  debt_gdp  "
        "life_exp  conflict"
    )
    print("-" * 88)

    for result in results:
        current = result.state
        print(
            f"{current.year:4d}  "
            f"{result.derived['gdp_growth']:7.2%}  "
            f"{result.derived['gdp_per_capita']:8.0f}  "
            f"{current.inflation:9.2%}  "
            f"{current.unemployment:12.2%}  "
            f"{current.debt_gdp:8.1%}  "
            f"{current.life_expectancy:8.2f}  "
            f"{current.conflict_risk:8.1%}"
        )
        if audit:
            for entry in result.audit_log:
                if entry.severity != "none":
                    print(
                        f"      [{entry.severity:11}] {entry.variable}: "
                        f"delta={entry.delta:+.6g} | {entry.note}"
                    )


def write_csv(results: list, path: Path) -> None:
    """Write a stable annual summary suitable for downstream analysis."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "year",
        "gdp_growth",
        "gdp_per_capita",
        "inflation",
        "unemployment",
        "debt_gdp",
        "life_expectancy",
        "conflict_risk",
        "political_stability_score",
        "school_life_expectancy",
        "hdi",
        "mean_years_schooling",
        "expected_years_schooling",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "year": result.state.year,
                    "gdp_growth": result.derived["gdp_growth"],
                    "gdp_per_capita": result.derived["gdp_per_capita"],
                    "inflation": result.state.inflation,
                    "unemployment": result.state.unemployment,
                    "debt_gdp": result.state.debt_gdp,
                    "life_expectancy": result.state.life_expectancy,
                    "conflict_risk": result.state.conflict_risk,
                    "political_stability_score": result.derived[
                        "political_stability_score"
                    ],
                    "school_life_expectancy": result.derived[
                        "school_life_expectancy"
                    ],
                    "hdi": result.reference["hdi"],
                    "mean_years_schooling": result.reference[
                        "mean_years_schooling"
                    ],
                    "expected_years_schooling": result.reference[
                        "expected_years_schooling"
                    ],
                }
            )


def main(argv: list[str] | None = None) -> int:
    """Run the command-line application and return a process status code."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.years < 0:
            raise ValueError("years must be non-negative")
        state = initialize_country(
            args.country,
            args.start_year,
            db_conn=args.database,
        )
        policy = policy_from_args(args)
        results = SimulationEngine.simulate(state, policy, args.years)
    except (FileNotFoundError, LookupError, ValueError) as exc:
        parser.error(str(exc))

    _print_results(state.country_code, state.year, results, args.audit)
    if args.output:
        write_csv(results, args.output)
        print(f"CSV output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
