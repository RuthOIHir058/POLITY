from engine.core.simulation_engine import SimulationEngine
from engine.core.simulation_step import SimulationStep


def test_simulation_step_facade_delegates_to_canonical_engine(
    baseline_state, baseline_policy
):
    canonical = SimulationEngine.step(baseline_state, baseline_policy)
    assert SimulationStep.step(baseline_state, baseline_policy) == canonical
    assert SimulationStep.run(baseline_state, baseline_policy) == canonical


def test_simulation_step_forwards_external_shocks(baseline_state, baseline_policy):
    shock = {"import_price_change": 0.08}
    assert SimulationStep.step(
        baseline_state, baseline_policy, shock
    ) == SimulationEngine.step(baseline_state, baseline_policy, shock)
