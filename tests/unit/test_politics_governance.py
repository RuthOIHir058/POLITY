from dataclasses import replace

import pytest

from engine.governance.capacity import (
    capacity_investment_factor,
    update_corruption,
    update_state_capacity,
)
from engine.politics.stability import (
    calibrate_conflict_intercept,
    conflict_gdp_penalty,
    evaluate_conflict_risk,
    stability_band,
)


def test_conflict_intercept_calibration_reproduces_wgi_target(baseline_state):
    historical_wgi = 0.50
    intercept = calibrate_conflict_intercept(baseline_state, historical_wgi)
    calibrated = replace(baseline_state, conflict_intercept=intercept)
    result = evaluate_conflict_risk(
        calibrated,
        calibrated.unemployment,
        calibrated.previous_gdp_growth,
        calibrated.gini,
        calibrated.inflation,
        0.0,
    )
    target = 1.0 - (historical_wgi + 2.5) / 5.0
    assert result.conflict_risk == pytest.approx(target)


def test_stability_bands_and_gdp_penalties():
    assert stability_band(0.20) == "STABLE"
    assert stability_band(0.40) == "STRESSED"
    assert stability_band(0.60) == "UNSTABLE"
    assert stability_band(0.80) == "CRISIS"
    assert conflict_gdp_penalty(0.20) == 0.0
    assert conflict_gdp_penalty(0.40) == pytest.approx(-0.005)
    assert conflict_gdp_penalty(0.60) == pytest.approx(-0.015)
    assert conflict_gdp_penalty(0.80) == pytest.approx(-0.032)


def test_capacity_investment_is_full_half_or_blocked():
    assert capacity_investment_factor(0.20) == 1.0
    assert capacity_investment_factor(0.40) == 0.5
    assert capacity_investment_factor(0.60) == 0.0


def test_state_capacity_equations_use_prior_conflict_band(baseline_state):
    stressed = replace(baseline_state, conflict_risk=0.40)
    update = update_state_capacity(stressed, admin_spend=0.02)
    expected_fiscal_delta = 0.020 * (0.02 / 0.02) * 0.5 - 0.025 * 0.30 - 0.01
    expected_legal_delta = 0.015 * (0.02 / 0.02) * 0.5 - 0.030 * 0.30 - 0.01
    assert update.fiscal_capacity == pytest.approx(0.60 + expected_fiscal_delta)
    assert update.legal_capacity == pytest.approx(0.60 + expected_legal_delta)

    unstable = replace(baseline_state, conflict_risk=0.60)
    degraded = update_state_capacity(unstable, admin_spend=0.10)
    assert dict(degraded.fiscal_causes)["admin_investment"] == 0.0
    assert dict(degraded.fiscal_causes)["conflict_degradation"] == pytest.approx(-0.05)
    assert dict(degraded.legal_causes)["conflict_degradation"] == pytest.approx(-0.08)


def test_corruption_update_matches_named_pushes_and_pull(baseline_state):
    state = replace(baseline_state, conflict_risk=0.50)
    update = update_corruption(state, gdp_per_capita_t=5_000.0)
    expected = (
        0.30
        + 0.030 * (0.50 - 0.40)
        + 0.010 * (0.50 - 5_000.0 / 20_000.0)
        - 0.020 * 0.60
    )
    assert update.corruption == pytest.approx(expected)
    assert sum(value for _, value in update.causes) == pytest.approx(
        update.corruption - state.corruption
    )
