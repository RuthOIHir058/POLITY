"""Layer 5 human-capital stock and transparent 15-year investment pipeline."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Sequence

from engine.core.constants import (
    DEFAULT_EDUCATION_SPEND_GDP,
    HC_BASE_INVESTMENT,
    HC_DEPRECIATION,
    HC_DIMINISHING_RETURN_COEFF,
    HC_PIPELINE_LAG,
    HC_SPEND_REFERENCE,
    HUMAN_CAPITAL_MAX,
    HUMAN_CAPITAL_MIN,
)
from engine.core.country_state import CountryState
from engine.core.helpers import clamp_with_adjustment


@dataclass(frozen=True)
class HumanCapitalUpdate:
    human_capital: float
    pipeline: deque[float]
    new_investment: float
    matured_investment: float
    depreciation: float
    causes: list[tuple[str, float]]


def compute_hc_investment(edu_spend_gdp: float, current_hc: float) -> float:
    spend_ratio = edu_spend_gdp / HC_SPEND_REFERENCE
    raw_investment = spend_ratio * HC_BASE_INVESTMENT
    diminishing_returns = 1.0 - HC_DIMINISHING_RETURN_COEFF * current_hc
    return raw_investment * diminishing_returns


def initialize_hc_pipeline(
    state: CountryState,
    historical_edu_spend: Sequence[float],
) -> deque[float]:
    history = [float(value) for value in historical_edu_spend]
    if len(history) >= HC_PIPELINE_LAG:
        spend_series = history[-HC_PIPELINE_LAG:]
    else:
        padding = history[0] if history else DEFAULT_EDUCATION_SPEND_GDP
        spend_series = [padding] * (HC_PIPELINE_LAG - len(history)) + history

    return deque(
        [
            compute_hc_investment(spend, state.human_capital)
            for spend in spend_series
        ],
        maxlen=HC_PIPELINE_LAG,
    )


def step_human_capital(
    state: CountryState,
    edu_spend_gdp: float,
) -> HumanCapitalUpdate:
    pipeline = deque(state.hc_pipeline, maxlen=HC_PIPELINE_LAG)
    matured = pipeline[0]
    new_investment = compute_hc_investment(
        edu_spend_gdp, state.human_capital
    )
    pipeline.append(new_investment)

    depreciation = HC_DEPRECIATION * state.human_capital
    raw_hc = state.human_capital + matured - depreciation
    human_capital_t, boundary_adjustment = clamp_with_adjustment(
        raw_hc, HUMAN_CAPITAL_MIN, HUMAN_CAPITAL_MAX
    )

    causes = [
        ("pipeline_matured_investment", matured),
        ("workforce_depreciation", -depreciation),
    ]
    if boundary_adjustment:
        causes.append(("range_clamp", boundary_adjustment))

    return HumanCapitalUpdate(
        human_capital=human_capital_t,
        pipeline=pipeline,
        new_investment=new_investment,
        matured_investment=matured,
        depreciation=depreciation,
        causes=causes,
    )
