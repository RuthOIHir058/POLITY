"""Layer 5 life-expectancy and school-life-expectancy equations."""

from __future__ import annotations

import math
from dataclasses import dataclass

from engine.core.constants import (
    LE_ADJUSTMENT_SPEED,
    LE_CEILING_BASE,
    LE_CEILING_INCOME_FLOOR,
    LE_CEILING_INCOME_SCALE,
    LE_CEILING_LOG_COEFF,
    LE_CEILING_MAX,
    LE_CEILING_MIN,
    LE_EDUCATION_COEFF,
    LE_HC_REFERENCE,
    LE_HEALTH_LOG_COEFF,
    LE_HEALTH_SPEND_SCALE,
    LE_INCOME_EFFECT_MAX,
    LE_INCOME_EFFECT_MIN,
    LE_INCOME_FINAL_WEIGHT,
    LE_INCOME_LOG_COEFF,
    LIFE_EXPECTANCY_MIN,
    LIFE_EXPECTANCY_UPDATE_MAX,
    SLE_HC_YEARS_MAX,
    SLE_MAX,
    SLE_MIN,
    SLE_SPENDING_COEFF,
    SLE_SPENDING_REFERENCE,
)
from engine.core.country_state import CountryState
from engine.core.helpers import clamp, clamp_with_adjustment


@dataclass(frozen=True)
class LifeExpectancyUpdate:
    life_expectancy: float
    ceiling: float
    target: float
    health_effect: float
    education_effect: float
    income_effect: float
    causes: list[tuple[str, float]]


@dataclass(frozen=True)
class SchoolLifeExpectancy:
    value: float
    base: float
    spending_boost: float
    causes: list[tuple[str, float]]


def update_life_expectancy(
    state: CountryState,
    health_spend: float,
    gdp_per_capita_t: float,
) -> LifeExpectancyUpdate:
    health_effect = LE_HEALTH_LOG_COEFF * math.log1p(
        health_spend * LE_HEALTH_SPEND_SCALE
    )
    education_effect = LE_EDUCATION_COEFF * (
        state.human_capital - LE_HC_REFERENCE
    )

    previous_gdp_per_capita = state.gdp / state.population
    income_log_change = math.log(gdp_per_capita_t) - math.log(
        previous_gdp_per_capita
    )
    income_effect = clamp(
        LE_INCOME_LOG_COEFF * income_log_change,
        LE_INCOME_EFFECT_MIN,
        LE_INCOME_EFFECT_MAX,
    )

    ceiling = LE_CEILING_BASE + LE_CEILING_LOG_COEFF * math.log10(
        max(
            gdp_per_capita_t / LE_CEILING_INCOME_SCALE,
            LE_CEILING_INCOME_FLOOR,
        )
        + 1.0
    )
    ceiling = clamp(ceiling, LE_CEILING_MIN, LE_CEILING_MAX)

    unconstrained_target = (
        state.life_expectancy + health_effect + education_effect
    )
    target = min(unconstrained_target, ceiling)
    ceiling_adjustment = target - unconstrained_target

    raw_life_expectancy = (
        state.life_expectancy
        + LE_ADJUSTMENT_SPEED * (target - state.life_expectancy)
        + LE_INCOME_FINAL_WEIGHT * income_effect
    )
    life_expectancy_t, boundary_adjustment = clamp_with_adjustment(
        raw_life_expectancy, LIFE_EXPECTANCY_MIN, LIFE_EXPECTANCY_UPDATE_MAX
    )

    causes = [
        ("health_spending", LE_ADJUSTMENT_SPEED * health_effect),
        ("education_health_behaviour", LE_ADJUSTMENT_SPEED * education_effect),
        ("income_change", LE_INCOME_FINAL_WEIGHT * income_effect),
    ]
    if ceiling_adjustment:
        causes.append(
            ("income_conditioned_le_ceiling", LE_ADJUSTMENT_SPEED * ceiling_adjustment)
        )
    if boundary_adjustment:
        causes.append(("range_clamp", boundary_adjustment))

    return LifeExpectancyUpdate(
        life_expectancy=life_expectancy_t,
        ceiling=ceiling,
        target=target,
        health_effect=health_effect,
        education_effect=education_effect,
        income_effect=income_effect,
        causes=causes,
    )


def compute_school_life_expectancy(
    human_capital_t: float,
    education_spend: float,
) -> SchoolLifeExpectancy:
    base = human_capital_t * SLE_HC_YEARS_MAX
    spending_boost = SLE_SPENDING_COEFF * (
        education_spend - SLE_SPENDING_REFERENCE
    )
    raw = base + spending_boost
    value, boundary_adjustment = clamp_with_adjustment(raw, SLE_MIN, SLE_MAX)
    causes = [
        ("human_capital_base", base),
        ("education_spending_boost", spending_boost),
    ]
    if boundary_adjustment:
        causes.append(("range_clamp", boundary_adjustment))
    return SchoolLifeExpectancy(
        value=value,
        base=base,
        spending_boost=spending_boost,
        causes=causes,
    )
