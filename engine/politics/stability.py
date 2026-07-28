"""Layer 3 political-stability filtration and conflict-risk equations."""

from __future__ import annotations

import math
from dataclasses import dataclass

from engine.core.constants import (
    CONFLICT_CALIBRATION_MAX,
    CONFLICT_CALIBRATION_MIN,
    CONFLICT_CAPACITY_PROTECT,
    CONFLICT_CRISIS_BASE_GDP_ADJ,
    CONFLICT_CRISIS_SLOPE,
    CONFLICT_GINI_COEFF,
    CONFLICT_GINI_THRESHOLD,
    CONFLICT_INFLATION_COEFF,
    CONFLICT_INFLATION_THRESHOLD,
    CONFLICT_MILITARY_SUPPRESS,
    CONFLICT_RECESSION_COEFF,
    CONFLICT_STABLE_MAX,
    CONFLICT_STRESSED_GDP_ADJ,
    CONFLICT_STRESSED_MAX,
    CONFLICT_UNEMPLOYMENT_BUFFER,
    CONFLICT_UNEMP_COEFF,
    CONFLICT_UNSTABLE_GDP_ADJ,
    CONFLICT_UNSTABLE_MAX,
    CONFLICT_URBAN_COEFF,
    CONFLICT_YOUTH_CENTER,
    CONFLICT_YOUTH_COEFF,
    CONFLICT_YOUTH_SCALE,
)
from engine.core.country_state import CountryState
from engine.core.helpers import clamp, logistic


@dataclass(frozen=True)
class ConflictRiskUpdate:
    conflict_risk: float
    political_stability_score: float
    eta: float
    band: str
    components: dict[str, float]


def stability_band(conflict_risk: float) -> str:
    if conflict_risk < CONFLICT_STABLE_MAX:
        return "STABLE"
    if conflict_risk < CONFLICT_STRESSED_MAX:
        return "STRESSED"
    if conflict_risk < CONFLICT_UNSTABLE_MAX:
        return "UNSTABLE"
    return "CRISIS"


def conflict_gdp_penalty(conflict_risk: float) -> float:
    """Return the next-year GDP adjustment for a persisted conflict risk."""

    if conflict_risk < CONFLICT_STABLE_MAX:
        return 0.0
    if conflict_risk < CONFLICT_STRESSED_MAX:
        return CONFLICT_STRESSED_GDP_ADJ
    if conflict_risk < CONFLICT_UNSTABLE_MAX:
        return CONFLICT_UNSTABLE_GDP_ADJ
    return CONFLICT_CRISIS_BASE_GDP_ADJ + CONFLICT_CRISIS_SLOPE * (
        conflict_risk - CONFLICT_UNSTABLE_MAX
    )


def conflict_eta_components(
    state: CountryState,
    unemployment_t: float,
    gdp_growth: float,
    gini_t: float,
    inflation_t: float,
    military_spend: float,
    *,
    intercept: float | None = None,
) -> dict[str, float]:
    youth_norm = (state.youth_share - CONFLICT_YOUTH_CENTER) / CONFLICT_YOUTH_SCALE
    unemployment_excess = max(
        0.0,
        unemployment_t
        - state.structural_unemployment
        - CONFLICT_UNEMPLOYMENT_BUFFER,
    )
    urban_youth = state.urban_pop_pct * max(0.0, youth_norm)
    gini_excess = max(0.0, gini_t - CONFLICT_GINI_THRESHOLD)
    recession_drag = max(0.0, -gdp_growth)
    inflation_stress = max(
        0.0, inflation_t - CONFLICT_INFLATION_THRESHOLD
    )

    return {
        "country_intercept": (
            state.conflict_intercept if intercept is None else intercept
        ),
        "youth_bulge": CONFLICT_YOUTH_COEFF * youth_norm,
        "unemployment_excess": CONFLICT_UNEMP_COEFF * unemployment_excess,
        "urban_youth_interaction": CONFLICT_URBAN_COEFF * urban_youth,
        "gini_excess": CONFLICT_GINI_COEFF * gini_excess,
        "recession_drag": CONFLICT_RECESSION_COEFF * recession_drag,
        "inflation_stress": CONFLICT_INFLATION_COEFF * inflation_stress,
        "legal_capacity_protection": -CONFLICT_CAPACITY_PROTECT
        * state.legal_capacity,
        "military_suppression": -CONFLICT_MILITARY_SUPPRESS * military_spend,
    }


def evaluate_conflict_risk(
    state: CountryState,
    unemployment_t: float,
    gdp_growth: float,
    gini_t: float,
    inflation_t: float,
    military_spend: float,
) -> ConflictRiskUpdate:
    components = conflict_eta_components(
        state,
        unemployment_t,
        gdp_growth,
        gini_t,
        inflation_t,
        military_spend,
    )
    eta = sum(components.values())
    risk = logistic(eta)
    return ConflictRiskUpdate(
        conflict_risk=risk,
        political_stability_score=2.5 - 5.0 * risk,
        eta=eta,
        band=stability_band(risk),
        components=components,
    )


def compute_conflict_risk(
    state: CountryState,
    unemployment_t: float,
    gdp_growth: float,
    gini_t: float,
    inflation_t: float,
    military_spend: float,
) -> float:
    return evaluate_conflict_risk(
        state,
        unemployment_t,
        gdp_growth,
        gini_t,
        inflation_t,
        military_spend,
    ).conflict_risk


def compute_conflict_eta_no_intercept(state: CountryState) -> float:
    """Baseline covariate sum used during country calibration.

    Historical military spending is not present in the V1 warehouse, so its
    baseline policy contribution is the guidebook-neutral value of zero.
    """

    components = conflict_eta_components(
        state,
        state.unemployment,
        state.previous_gdp_growth
        if state.previous_gdp_growth is not None
        else state.potential_growth,
        state.gini,
        state.inflation,
        0.0,
        intercept=0.0,
    )
    return sum(components.values())


def calibrate_conflict_intercept(
    state: CountryState,
    historical_stability_wgi: float,
) -> float:
    target_risk = clamp(
        1.0 - (historical_stability_wgi + 2.5) / 5.0,
        CONFLICT_CALIBRATION_MIN,
        CONFLICT_CALIBRATION_MAX,
    )
    target_logit = math.log(target_risk / (1.0 - target_risk))
    return target_logit - compute_conflict_eta_no_intercept(state)


def conflict_risk_from_wgi(historical_stability_wgi: float) -> float:
    return clamp(
        1.0 - (historical_stability_wgi + 2.5) / 5.0,
        CONFLICT_CALIBRATION_MIN,
        CONFLICT_CALIBRATION_MAX,
    )
