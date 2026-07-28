"""Run identical simulations twice and require exact serialized equality."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

from engine.cli import DEFAULT_POLICY
from engine.core.initialize_country import initialize_country
from engine.core.simulation_engine import SimulationEngine
from tools.validation._common import database_parser, require_database


def _canonical_results(results) -> str:
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
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def main(argv: list[str] | None = None) -> int:
    parser = database_parser(__doc__)
    parser.add_argument("--country", default="KEN")
    parser.add_argument("--year", type=int, default=2015)
    parser.add_argument("--years", type=int, default=20)
    args = parser.parse_args(argv)
    database = require_database(args.database)

    initial = initialize_country(args.country, args.year, database)
    snapshot = initial.clone()
    first = SimulationEngine.simulate(initial, DEFAULT_POLICY, args.years)
    second = SimulationEngine.simulate(initial, DEFAULT_POLICY, args.years)
    first_json = _canonical_results(first)
    second_json = _canonical_results(second)
    if first_json != second_json:
        raise SystemExit("FAIL: identical inputs produced different results")
    if initial != snapshot:
        raise SystemExit("FAIL: simulation mutated its input CountryState")

    fingerprint = hashlib.sha256(first_json.encode("utf-8")).hexdigest()
    print(f"PASS exact deterministic equality ({len(first)} years)")
    print(f"canonical result fingerprint: {fingerprint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
