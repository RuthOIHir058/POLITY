from copy import deepcopy
from dataclasses import replace

import pytest

from engine.core.policy_inputs import PolicyInputs
from engine.core.simulation_engine import SimulationEngine
from engine.core.variable_registry import TIER1_VARIABLES, TIER2_VARIABLES, TIER3_VARIABLES


def test_phase_sequence_contains_all_24_steps():
    assert len(SimulationEngine.PHASES) == 24
    assert SimulationEngine.PHASES[0] == "validate_policy_inputs"
    assert SimulationEngine.PHASES[18] == "update_trade_openness"
    assert SimulationEngine.PHASES[-1] == "increment_year_and_return"


def test_step_is_deterministic_and_does_not_mutate_input(
    baseline_state, baseline_policy
):
    original = deepcopy(baseline_state)
    first = SimulationEngine.step(baseline_state, baseline_policy)
    second = SimulationEngine.step(baseline_state, baseline_policy)

    assert baseline_state == original
    assert first == second
    assert first.state is not baseline_state
    assert first.state.year == baseline_state.year + 1


def test_step_returns_complete_tiers_and_audit_coverage(
    baseline_state, baseline_policy
):
    result = SimulationEngine.step(baseline_state, baseline_policy)
    assert TIER2_VARIABLES <= result.derived.keys()
    assert TIER3_VARIABLES == result.reference.keys()

    audited = {entry.variable for entry in result.audit_log}
    assert TIER1_VARIABLES <= audited
    assert TIER2_VARIABLES <= audited
    assert TIER3_VARIABLES <= audited
    assert all(entry.causes for entry in result.audit_log)


def test_calibration_constants_are_not_updated(baseline_state, baseline_policy):
    result = SimulationEngine.step(baseline_state, baseline_policy)
    for field in (
        "potential_growth",
        "structural_unemployment",
        "urbanization_capacity",
        "conflict_intercept",
    ):
        assert getattr(result.state, field) == getattr(baseline_state, field)


def test_explicit_import_shock_has_deterministic_passthrough(
    baseline_state, baseline_policy
):
    no_shock = SimulationEngine.step(baseline_state, baseline_policy)
    shocked = SimulationEngine.step(
        baseline_state,
        baseline_policy,
        {"import_price_change": 0.10},
    )
    expected_difference = 0.30 * 0.10 * baseline_state.trade_openness
    assert shocked.state.inflation - no_shock.state.inflation == pytest.approx(
        expected_difference
    )


def test_step23_stabilizers_recompute_effective_policy(baseline_state):
    state = replace(
        baseline_state,
        debt_gdp=0.95,
        risk_premium=0.06,
        unemployment=0.25,
        conflict_risk=0.20,
    )
    policy = PolicyInputs(
        tax_rate=0.05,
        total_expenditure_gdp=0.65,
        health_share=0.10,
        education_share=0.10,
        infrastructure_share=0.50,
        social_transfers_share=0.01,
        admin_share=0.15,
        military_share=0.14,
        inflation_target=0.02,
        trade_policy=0.0,
    )
    result = SimulationEngine.step(state, policy)

    assert result.derived["sovereign_consolidation"] > 0.0
    assert result.derived["safety_net_reallocation"] > 0.0
    assert result.derived["effective_social_transfers_spend_gdp"] == pytest.approx(
        0.01
    )
    assert result.derived["stabilizer_recomputed"] == 1.0
    audited = {entry.variable for entry in result.audit_log}
    assert "effective_expenditure_gdp" in audited
    assert "effective_social_transfers_gdp" in audited


def test_twenty_year_simulation_stays_within_registry_bounds(
    baseline_state, baseline_policy
):
    results = SimulationEngine.simulate(baseline_state, baseline_policy, 20)
    assert len(results) == 20
    assert results[-1].state.year == baseline_state.year + 20
    for result in results:
        state = result.state
        assert state.gdp > 0.0
        assert state.population > 0.0
        assert -0.05 <= state.inflation <= 2.0
        assert 0.0 <= state.unemployment <= 0.40
        assert 0.0 <= state.debt_gdp <= 3.0
        assert 0.0 <= state.risk_premium <= 0.25
        assert 0.0 <= state.conflict_risk <= 1.0
