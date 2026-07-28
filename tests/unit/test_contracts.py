from collections import deque
from copy import deepcopy
from dataclasses import fields

import pytest

from engine.core.country_state import CountryState
from engine.core.policy_inputs import PolicyInputs
from engine.core.variable_registry import (
    CALIBRATION_VARIABLES,
    INTERNAL_STATE_VARIABLES,
    TIER1_VARIABLES,
    TIER2_VARIABLES,
    TIER3_VARIABLES,
)
from engine.policy.validation import validate_policy


def test_country_state_is_canonical_and_clone_is_deep(baseline_state):
    field_names = {field.name for field in fields(CountryState)}
    assert TIER1_VARIABLES <= field_names
    assert CALIBRATION_VARIABLES <= field_names
    assert INTERNAL_STATE_VARIABLES <= field_names
    assert "gdp_current_usd" not in field_names
    assert "gdp_per_capita" not in field_names
    assert "hdi" not in field_names

    original = deepcopy(baseline_state)
    cloned = baseline_state.clone()
    cloned.hc_pipeline.append(0.123)
    assert baseline_state == original
    assert cloned.hc_pipeline != baseline_state.hc_pipeline


def test_state_rejects_out_of_range_values(baseline_state):
    values = dict(vars(baseline_state))
    values["inflation"] = 3.0
    with pytest.raises(ValueError, match="inflation"):
        CountryState(**values)


def test_policy_validation_accepts_valid_policy(baseline_policy):
    assert validate_policy(baseline_policy) == []


@pytest.mark.parametrize(
    "updates, message",
    [
        ({"tax_rate": 0.01}, "Tax rate"),
        ({"total_expenditure_gdp": 0.90}, "Total expenditure"),
        ({"trade_policy": 1.1}, "Trade policy"),
        ({"inflation_target": 3.0}, "Inflation target"),
        ({"health_share": 0.50}, "Expenditure shares"),
    ],
)
def test_policy_validation_rejects_invalid_dimensions(
    baseline_policy, updates, message
):
    policy = baseline_policy.with_updates(**updates)
    with pytest.raises(ValueError, match=message):
        validate_policy(policy)


def test_registry_tiers_match_specification_names():
    assert {
        "gdp_growth",
        "gdp_per_capita",
        "output_gap",
        "tax_revenue_gdp",
        "primary_balance_gdp",
        "conflict_risk",
        "political_stability_score",
        "school_life_expectancy",
    } == TIER2_VARIABLES
    assert {
        "hdi",
        "mean_years_schooling",
        "expected_years_schooling",
    } == TIER3_VARIABLES
