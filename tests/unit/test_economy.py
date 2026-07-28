from dataclasses import replace

import pytest

from engine.economy.fiscal import (
    compute_fiscal_flows,
    debt_risk_function,
    update_debt,
    update_risk_premium,
)
from engine.economy.macro import (
    compute_gdp_growth,
    compute_output_gap,
    update_inflation,
    update_unemployment,
)
from engine.global_context.shocks import ExternalShocks
from engine.trade.openness import update_trade_openness


def test_trade_openness_convergence(baseline_state, baseline_policy):
    update = update_trade_openness(baseline_state, baseline_policy)
    target = 0.80 * (1.0 + 0.30 * 0.50)
    expected = 0.80 + 0.20 * (target - 0.80)
    assert update.target == pytest.approx(target)
    assert update.trade_openness == pytest.approx(expected)


def test_gdp_growth_decomposition_matches_equation(
    baseline_state, baseline_policy
):
    trade = update_trade_openness(baseline_state, baseline_policy)
    human_capital_t = 0.601
    growth = compute_gdp_growth(
        baseline_state,
        human_capital_t,
        trade.trade_openness,
        infra_spend_gdp=0.06,
    )
    expected = (
        0.03
        + 0.33 * (0.06 - 0.05)
        + (0.33 / 15.0) * (0.001) * 50.0
        + 0.03 * (0.60 - 0.50)
        + 0.10 * (trade.trade_openness - 0.80)
    )
    assert growth.conflict_adjustment == 0.0
    assert growth.gdp_growth == pytest.approx(expected)
    assert sum(value for _, value in growth.causes) == pytest.approx(expected)


def test_conflict_penalty_is_piecewise_not_multiplicative(
    baseline_state, baseline_policy
):
    state = replace(baseline_state, conflict_risk=0.60)
    trade = update_trade_openness(state, baseline_policy)
    growth = compute_gdp_growth(
        state, state.human_capital, trade.trade_openness, 0.05
    )
    assert growth.conflict_adjustment == pytest.approx(-0.015)
    assert growth.gdp_growth == pytest.approx(growth.gdp_growth_raw - 0.015)


def test_output_gap_normalizes_and_clamps():
    assert compute_output_gap(0.04, 0.03).value == pytest.approx(0.30)
    assert compute_output_gap(0.0315, 0.03).value == pytest.approx(0.05)


def test_hybrid_nkpc_terms(baseline_state, baseline_policy):
    update = update_inflation(
        baseline_state,
        baseline_policy,
        output_gap=0.10,
        external_shocks=ExternalShocks(import_price_change=0.10),
    )
    expected = 0.50 * 0.04 + 0.30 * 0.02 + 0.08 * 0.10 + 0.30 * 0.10 * 0.80
    assert update.inflation == pytest.approx(expected)
    assert sum(value for _, value in update.causes) == pytest.approx(expected)


def test_okun_law_and_structural_floor(baseline_state):
    update = update_unemployment(baseline_state, gdp_growth=0.05)
    assert update.unemployment == pytest.approx(0.08 - 0.40 * (0.05 - 0.03))

    boom = update_unemployment(baseline_state, gdp_growth=0.50)
    assert boom.unemployment == pytest.approx(baseline_state.structural_unemployment)


def test_fiscal_flows_scale_tax_collection_by_capacity(
    baseline_state, baseline_policy
):
    flows = compute_fiscal_flows(baseline_state, baseline_policy)
    assert flows.tax_revenue_gdp == pytest.approx(0.40 * 0.60)
    assert flows.primary_balance_gdp == pytest.approx(0.24 - 0.30)
    assert flows.education_spend == pytest.approx(0.06)


def test_debt_budget_constraint_and_audit_decomposition(
    baseline_state, baseline_policy
):
    flows = compute_fiscal_flows(baseline_state, baseline_policy)
    debt = update_debt(
        baseline_state,
        gdp_growth=0.04,
        inflation_t=0.03,
        primary_balance_gdp=flows.primary_balance_gdp,
    )
    expected = ((1.0 + 0.025) / (1.0 + 0.07)) * 0.50 - (-0.06)
    assert debt.debt_gdp == pytest.approx(expected)
    assert sum(value for _, value in debt.causes) == pytest.approx(
        debt.debt_gdp - baseline_state.debt_gdp
    )


def test_piecewise_debt_risk_and_autoregression(baseline_state):
    assert debt_risk_function(0.30) == 0.0
    assert debt_risk_function(0.50) == pytest.approx(0.0025)
    assert debt_risk_function(0.75) == pytest.approx(0.025)
    assert debt_risk_function(1.00) == pytest.approx(0.046)

    update = update_risk_premium(baseline_state, 0.75)
    assert update.risk_premium == pytest.approx(0.85 * 0.005 + 0.025)
