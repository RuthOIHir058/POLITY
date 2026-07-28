"""Layer 4 fiscal flows, debt dynamics, and sovereign risk."""

from __future__ import annotations

from dataclasses import dataclass

from engine.core.constants import (
    DEBT_GDP_MAX,
    DEBT_GDP_MIN,
    DEBT_RISK_EXPONENTIAL_COEFF,
    DEBT_RISK_HIGH_MAX,
    DEBT_RISK_HIGH_THRESHOLD,
    DEBT_RISK_LOW_MAX,
    DEBT_RISK_LOW_THRESHOLD,
    DEBT_RISK_MID_THRESHOLD,
    RISK_FREE_RATE,
    RISK_PREMIUM_MAX,
    RISK_PREMIUM_MIN,
    RP_AUTOREGRESSION,
)
from engine.core.country_state import CountryState
from engine.core.helpers import clamp_with_adjustment
from engine.core.policy_inputs import PolicyInputs
from engine.policy.validation import expenditure_breakdown


@dataclass(frozen=True)
class FiscalFlows:
    tax_revenue_gdp: float
    total_expenditure_gdp: float
    primary_balance_gdp: float
    health_spend: float
    education_spend: float
    infra_spend: float
    transfers_spend: float
    admin_spend: float
    military_spend: float


@dataclass(frozen=True)
class DebtUpdate:
    debt_gdp: float
    nominal_interest: float
    nominal_gdp_growth: float
    causes: list[tuple[str, float]]


@dataclass(frozen=True)
class RiskPremiumUpdate:
    risk_premium: float
    debt_risk: float
    causes: list[tuple[str, float]]


def compute_fiscal_flows(
    state: CountryState,
    policy: PolicyInputs,
) -> FiscalFlows:
    spends = expenditure_breakdown(policy)
    tax_revenue_gdp = policy.tax_rate * state.fiscal_capacity
    primary_balance_gdp = (
        tax_revenue_gdp - policy.total_expenditure_gdp
    )
    return FiscalFlows(
        tax_revenue_gdp=tax_revenue_gdp,
        total_expenditure_gdp=policy.total_expenditure_gdp,
        primary_balance_gdp=primary_balance_gdp,
        **spends,
    )


def update_debt(
    state: CountryState,
    gdp_growth: float,
    inflation_t: float,
    primary_balance_gdp: float,
) -> DebtUpdate:
    nominal_interest = RISK_FREE_RATE + state.risk_premium
    nominal_gdp_growth = gdp_growth + inflation_t
    denominator = 1.0 + nominal_gdp_growth
    if denominator <= 0.0:
        raise ValueError(
            "Debt equation undefined because nominal GDP growth is <= -100%"
        )

    raw = (
        ((1.0 + nominal_interest) / denominator) * state.debt_gdp
        - primary_balance_gdp
    )
    debt_t, boundary_adjustment = clamp_with_adjustment(
        raw, DEBT_GDP_MIN, DEBT_GDP_MAX
    )

    interest_contribution = (
        state.debt_gdp * nominal_interest / denominator
    )
    growth_contribution = state.debt_gdp * (1.0 / denominator - 1.0)
    causes = [
        ("interest_burden", interest_contribution),
        ("growth_denominator", growth_contribution),
        ("primary_balance", -primary_balance_gdp),
    ]
    if boundary_adjustment:
        causes.append(("range_clamp", boundary_adjustment))

    return DebtUpdate(
        debt_gdp=debt_t,
        nominal_interest=nominal_interest,
        nominal_gdp_growth=nominal_gdp_growth,
        causes=causes,
    )


def debt_risk_function(debt_gdp: float) -> float:
    if debt_gdp < DEBT_RISK_LOW_THRESHOLD:
        return 0.0
    if debt_gdp < DEBT_RISK_MID_THRESHOLD:
        return DEBT_RISK_LOW_MAX * (
            debt_gdp - DEBT_RISK_LOW_THRESHOLD
        ) / (DEBT_RISK_MID_THRESHOLD - DEBT_RISK_LOW_THRESHOLD)
    if debt_gdp < DEBT_RISK_HIGH_THRESHOLD:
        return DEBT_RISK_LOW_MAX + (
            DEBT_RISK_HIGH_MAX - DEBT_RISK_LOW_MAX
        ) * (debt_gdp - DEBT_RISK_MID_THRESHOLD) / (
            DEBT_RISK_HIGH_THRESHOLD - DEBT_RISK_MID_THRESHOLD
        )
    return DEBT_RISK_HIGH_MAX + DEBT_RISK_EXPONENTIAL_COEFF * (
        debt_gdp - DEBT_RISK_HIGH_THRESHOLD
    ) ** 2


def update_risk_premium(
    state: CountryState,
    debt_gdp_t: float,
) -> RiskPremiumUpdate:
    autoregressive = RP_AUTOREGRESSION * state.risk_premium
    debt_risk = debt_risk_function(debt_gdp_t)
    raw = autoregressive + debt_risk
    risk_t, boundary_adjustment = clamp_with_adjustment(
        raw, RISK_PREMIUM_MIN, RISK_PREMIUM_MAX
    )
    causes = [
        ("autoregressive_carryover", autoregressive),
        ("debt_risk_function", debt_risk),
    ]
    if boundary_adjustment:
        causes.append(("range_clamp", boundary_adjustment))
    return RiskPremiumUpdate(
        risk_premium=risk_t,
        debt_risk=debt_risk,
        causes=causes,
    )
