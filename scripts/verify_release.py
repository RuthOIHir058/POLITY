"""Run deterministic release-level model checks and emit a machine-readable report."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.core.initialize_country import initialize_country
from engine.core.policy_inputs import PolicyInputs
from engine.core.simulation_engine import SimulationEngine
from engine.data.country_loader import DEFAULT_DB_PATH


def _display_path(path: Path) -> str:
    """Return a publication-safe path without local workstation prefixes."""

    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.name


def canonical_results(results) -> str:
    payload = []
    for result in results:
        state = asdict(result.state)
        state["hc_pipeline"] = list(result.state.hc_pipeline)
        payload.append(
            {
                "state": state,
                "derived": result.derived,
                "reference": result.reference,
                "audit_log": [asdict(entry) for entry in result.audit_log],
            }
        )
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)


def run(database: Path) -> dict[str, object]:
    policy = PolicyInputs(
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

    with sqlite3.connect(database) as connection:
        codes = [row[0] for row in connection.execute("SELECT iso3 FROM countries ORDER BY iso3")]
        successful: list[str] = []
        failures: list[dict[str, str]] = []
        for code in codes:
            try:
                initial = initialize_country(code, 2015, db_conn=connection)
                SimulationEngine.simulate(initial, policy, 20)
                successful.append(code)
            except (LookupError, ValueError, ArithmeticError) as exc:
                failures.append(
                    {"country_code": code, "error_type": type(exc).__name__, "message": str(exc)}
                )

        kenya_initial = initialize_country("KEN", 2015, db_conn=connection)
        initial_snapshot = kenya_initial.clone()
        first = SimulationEngine.simulate(kenya_initial, policy, 20)
        second = SimulationEngine.simulate(kenya_initial, policy, 20)

    first_json = canonical_results(first)
    second_json = canonical_results(second)
    digest = hashlib.sha256(first_json.encode("utf-8")).hexdigest()
    exact_match = first_json == second_json
    input_unchanged = kenya_initial == initial_snapshot
    if not exact_match or not input_unchanged:
        raise RuntimeError("determinism or input immutability check failed")

    final = first[-1]
    return {
        "database": _display_path(database),
        "country_records": len(codes),
        "countries_initialized_and_simulated_20_years": len(successful),
        "countries_not_initializable_from_required_fields": len(failures),
        "successful_country_codes": successful,
        "failure_examples": failures[:20],
        "determinism": {
            "country_code": "KEN",
            "start_year": 2015,
            "years": 20,
            "exact_serialized_match": exact_match,
            "input_state_unchanged": input_unchanged,
            "sha256": digest,
        },
        "kenya_final_2035": {
            "gdp_per_capita": final.derived["gdp_per_capita"],
            "inflation": final.state.inflation,
            "unemployment": final.state.unemployment,
            "debt_gdp": final.state.debt_gdp,
            "life_expectancy": final.state.life_expectancy,
            "conflict_risk": final.state.conflict_risk,
            "audit_entries": len(final.audit_log),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    report = run(args.database)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
