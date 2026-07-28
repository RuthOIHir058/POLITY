from collections import deque

import pytest

from engine.core.country_state import CountryState
from engine.core.policy_inputs import PolicyInputs


@pytest.fixture
def baseline_state() -> CountryState:
    return CountryState(
        country_code="TST",
        year=2020,
        gdp=100_000_000_000.0,
        inflation=0.04,
        unemployment=0.08,
        debt_gdp=0.50,
        risk_premium=0.005,
        fiscal_capacity=0.60,
        legal_capacity=0.60,
        corruption=0.30,
        population=50_000_000.0,
        youth_share=0.30,
        working_age_share=0.65,
        elderly_share=0.05,
        urban_pop_pct=0.50,
        human_capital=0.60,
        life_expectancy=70.0,
        gini=0.40,
        trade_openness=0.80,
        conflict_risk=0.20,
        hc_pipeline=deque([0.001] * 15, maxlen=15),
        potential_growth=0.03,
        structural_unemployment=0.05,
        urbanization_capacity=0.90,
        conflict_intercept=-1.5,
        previous_gdp_growth=0.04,
    )


@pytest.fixture
def baseline_policy() -> PolicyInputs:
    return PolicyInputs(
        tax_rate=0.40,
        total_expenditure_gdp=0.30,
        health_share=0.15,
        education_share=0.20,
        infrastructure_share=0.20,
        social_transfers_share=0.20,
        admin_share=0.15,
        military_share=0.10,
        inflation_target=0.02,
        trade_policy=0.50,
    )
