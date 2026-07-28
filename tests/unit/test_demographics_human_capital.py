from collections import deque
from dataclasses import replace

import pytest

from engine.society.demographics import update_demographics
from engine.society.human_capital import (
    compute_hc_investment,
    initialize_hc_pipeline,
    step_human_capital,
)
from engine.society.urbanization import update_urbanization


def test_demographic_equations_match_guidebook(baseline_state):
    update = update_demographics(baseline_state)
    expected_youth_delta = -0.0008 * (70.0 - 65.0) - 0.0015 * (0.60 - 0.50)
    expected_elderly_delta = 0.0012 * (70.0 - 65.0)
    expected_population_growth = 0.30 * 0.045 - 1.0 / 70.0

    assert update.youth_share == pytest.approx(0.30 + expected_youth_delta)
    assert update.elderly_share == pytest.approx(0.05 + expected_elderly_delta)
    assert update.working_age_share == pytest.approx(
        1.0 - update.youth_share - update.elderly_share
    )
    assert update.population_growth == pytest.approx(expected_population_growth)
    assert update.population == pytest.approx(
        50_000_000.0 * (1.0 + expected_population_growth)
    )


def test_urbanization_base_and_wage_pull_are_separate(baseline_state):
    update = update_urbanization(baseline_state)
    saturation = 0.50 * (1.0 - 0.50 / 0.90)
    base = 0.03 * saturation
    wage = 0.03 * 10.0 * (0.04 - 0.03) * saturation
    assert update.delta == pytest.approx(base + wage)
    assert dict(update.causes)["logistic_base_migration"] == pytest.approx(base)
    assert dict(update.causes)["wage_differential_pull"] == pytest.approx(wage)


def test_hc_investment_and_pipeline_initialization(baseline_state):
    expected = (0.05 / 0.05) * 0.002 * (1.0 - 0.60 * 0.60)
    assert compute_hc_investment(0.05, 0.60) == pytest.approx(expected)

    pipeline = initialize_hc_pipeline(baseline_state, [0.03, 0.04])
    assert len(pipeline) == 15
    assert pipeline[0] == pytest.approx(
        compute_hc_investment(0.03, baseline_state.human_capital)
    )
    assert pipeline[-1] == pytest.approx(
        compute_hc_investment(0.04, baseline_state.human_capital)
    )


def test_hc_step_captures_oldest_before_append(baseline_state):
    update = step_human_capital(baseline_state, 0.05)
    assert update.matured_investment == pytest.approx(0.001)
    assert update.pipeline[-1] == pytest.approx(
        compute_hc_investment(0.05, baseline_state.human_capital)
    )
    assert update.human_capital == pytest.approx(
        0.60 + 0.001 - 0.003 * 0.60
    )


def test_new_education_investment_matures_after_fifteen_queue_advances(
    baseline_state,
):
    state = replace(
        baseline_state,
        human_capital=0.0,
        hc_pipeline=deque([0.0] * 15, maxlen=15),
    )
    first_investment = compute_hc_investment(0.05, 0.0)

    for _ in range(15):
        update = step_human_capital(state, 0.05)
        assert update.matured_investment == 0.0
        state = replace(
            state,
            human_capital=update.human_capital,
            hc_pipeline=update.pipeline,
        )

    update = step_human_capital(state, 0.05)
    assert update.matured_investment == pytest.approx(first_investment)
