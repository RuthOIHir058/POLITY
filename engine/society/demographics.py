"""Layer 5 aggregate demographic equations for POLITY V1."""

from __future__ import annotations

from dataclasses import dataclass

from engine.core.constants import (
    DEMOGRAPHIC_HC_REFERENCE,
    DEMOGRAPHIC_LE_REFERENCE,
    ELDERLY_LE_COEFF,
    ELDERLY_SHARE_MAX,
    ELDERLY_SHARE_MIN,
    POPULATION_BIRTHS_PROXY_COEFF,
    WORKING_AGE_SHARE_MAX,
    WORKING_AGE_SHARE_MIN,
    YOUTH_EDUCATION_FERTILITY_COEFF,
    YOUTH_LE_FERTILITY_COEFF,
    YOUTH_SHARE_MAX,
    YOUTH_SHARE_MIN,
)
from engine.core.country_state import CountryState
from engine.core.helpers import clamp_with_adjustment


@dataclass(frozen=True)
class DemographicsUpdate:
    youth_share: float
    working_age_share: float
    elderly_share: float
    population: float
    population_growth: float
    youth_causes: list[tuple[str, float]]
    working_causes: list[tuple[str, float]]
    elderly_causes: list[tuple[str, float]]
    population_causes: list[tuple[str, float]]


def update_demographics(state: CountryState) -> DemographicsUpdate:
    delta_youth_le = YOUTH_LE_FERTILITY_COEFF * (
        state.life_expectancy - DEMOGRAPHIC_LE_REFERENCE
    )
    delta_youth_hc = YOUTH_EDUCATION_FERTILITY_COEFF * (
        state.human_capital - DEMOGRAPHIC_HC_REFERENCE
    )
    raw_youth = state.youth_share + delta_youth_le + delta_youth_hc
    youth_share_t, youth_clamp = clamp_with_adjustment(
        raw_youth, YOUTH_SHARE_MIN, YOUTH_SHARE_MAX
    )

    delta_elderly_le = ELDERLY_LE_COEFF * (
        state.life_expectancy - DEMOGRAPHIC_LE_REFERENCE
    )
    raw_elderly = state.elderly_share + delta_elderly_le
    elderly_share_t, elderly_clamp = clamp_with_adjustment(
        raw_elderly, ELDERLY_SHARE_MIN, ELDERLY_SHARE_MAX
    )

    raw_working = 1.0 - youth_share_t - elderly_share_t
    working_age_share_t, working_clamp = clamp_with_adjustment(
        raw_working, WORKING_AGE_SHARE_MIN, WORKING_AGE_SHARE_MAX
    )

    births_rate = state.youth_share * POPULATION_BIRTHS_PROXY_COEFF
    deaths_rate = -(1.0 / state.life_expectancy)
    population_growth = births_rate + deaths_rate
    births_absolute = state.population * births_rate
    deaths_absolute = state.population * deaths_rate
    population_t = state.population * (1.0 + population_growth)

    youth_causes = [
        ("le_fertility_effect", delta_youth_le),
        ("education_fertility_effect", delta_youth_hc),
    ]
    if youth_clamp:
        youth_causes.append(("range_clamp", youth_clamp))

    elderly_causes = [("longevity_aging_effect", delta_elderly_le)]
    if elderly_clamp:
        elderly_causes.append(("range_clamp", elderly_clamp))

    working_causes = [
        ("cohort_residual", raw_working - state.working_age_share),
    ]
    if working_clamp:
        working_causes.append(("range_clamp", working_clamp))

    return DemographicsUpdate(
        youth_share=youth_share_t,
        working_age_share=working_age_share_t,
        elderly_share=elderly_share_t,
        population=population_t,
        population_growth=population_growth,
        youth_causes=youth_causes,
        working_causes=working_causes,
        elderly_causes=elderly_causes,
        population_causes=[
            ("births_proxy", births_absolute),
            ("deaths_proxy", deaths_absolute),
        ],
    )
