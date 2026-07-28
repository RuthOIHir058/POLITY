import math

import pytest

from engine.society.health import (
    compute_school_life_expectancy,
    update_life_expectancy,
)
from engine.society.inequality import update_gini
from engine.society.reference_metrics import compute_reference_metrics


def test_gini_persistent_structural_update(baseline_state):
    update = update_gini(
        baseline_state,
        inflation_t=0.10,
        unemployment_t=0.10,
        transfers_spend=0.08,
    )
    drivers = (
        0.005 * (0.10 - 0.05)
        + 0.003 * (0.10 - 0.05)
        - 0.008 * (0.60 - 0.50)
        + 0.0
        - 0.010 * (0.08 - 0.05)
    )
    expected = 0.40 + 0.10 * drivers
    assert update.gini == pytest.approx(expected)
    assert sum(value for _, value in update.causes) == pytest.approx(
        update.gini - baseline_state.gini
    )


def test_life_expectancy_preston_delta(baseline_state):
    gdp_pc_t = 2_100.0
    update = update_life_expectancy(
        baseline_state, health_spend=0.04, gdp_per_capita_t=gdp_pc_t
    )
    health = 0.30 * math.log1p(0.04 * 100.0)
    education = 0.15 * (0.60 - 0.50)
    previous_gdp_pc = baseline_state.gdp / baseline_state.population
    income = max(
        -1.0,
        min(1.0, 2.0 * (math.log(gdp_pc_t) - math.log(previous_gdp_pc))),
    )
    ceiling = 60.0 + 18.0 * math.log10(max(gdp_pc_t / 1000.0, 0.1) + 1.0)
    ceiling = max(45.0, min(87.0, ceiling))
    target = min(70.0 + health + education, ceiling)
    expected = 70.0 + 0.30 * (target - 70.0) + 0.1 * income
    expected = max(30.0, min(87.0, expected))
    assert update.life_expectancy == pytest.approx(expected)
    assert sum(value for _, value in update.causes) == pytest.approx(
        update.life_expectancy - baseline_state.life_expectancy
    )


def test_school_life_and_reference_metrics_are_display_only():
    school = compute_school_life_expectancy(0.60, 0.05)
    assert school.value == pytest.approx(0.60 * 18.0 + 2.0 * (0.05 - 0.04))

    reference = compute_reference_metrics(
        gdp_per_capita=10_000.0,
        life_expectancy=75.0,
        human_capital=0.60,
        school_life_expectancy=school.value,
    )
    assert reference.mean_years_schooling == pytest.approx(9.0)
    assert reference.expected_years_schooling == pytest.approx(school.value)
    assert 0.0 <= reference.hdi <= 1.0
