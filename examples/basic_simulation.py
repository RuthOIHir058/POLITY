"""Run a ten-year deterministic simulation using the bundled Kenya baseline."""

from engine.cli import DEFAULT_POLICY
from engine.core.initialize_country import initialize_country
from engine.core.simulation_engine import SimulationEngine


def main() -> int:
    initial = initialize_country("KEN", 2015)
    results = SimulationEngine.simulate(initial, DEFAULT_POLICY, years=10)
    final = results[-1]
    print(f"Start year: {initial.year}")
    print(f"End year: {final.state.year}")
    print(f"GDP per capita: {final.derived['gdp_per_capita']:.2f}")
    print(f"Inflation: {final.state.inflation:.2%}")
    print(f"Conflict risk: {final.state.conflict_risk:.2%}")
    print(f"Audit entries in final year: {len(final.audit_log)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
