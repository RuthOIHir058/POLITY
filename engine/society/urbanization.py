"""Layer 5 logistic urbanization with Harris-Todaro wage-gap proxy."""

from __future__ import annotations

from dataclasses import dataclass

from engine.core.constants import (
    URBANIZATION_K,
    URBANIZATION_WAGE_GAP_MULTIPLIER,
)
from engine.core.country_state import CountryState
from engine.core.helpers import clamp_with_adjustment


@dataclass(frozen=True)
class UrbanizationUpdate:
    urban_pop_pct: float
    delta: float
    causes: list[tuple[str, float]]


def update_urbanization(state: CountryState) -> UrbanizationUpdate:
    previous_growth = (
        state.previous_gdp_growth
        if state.previous_gdp_growth is not None
        else state.potential_growth
    )
    wage_gap = max(0.0, previous_growth - state.potential_growth)
    u = state.urban_pop_pct
    saturation = u * (1.0 - u / state.urbanization_capacity)

    base_contribution = URBANIZATION_K * saturation
    wage_contribution = (
        URBANIZATION_K
        * URBANIZATION_WAGE_GAP_MULTIPLIER
        * wage_gap
        * saturation
    )
    raw = u + base_contribution + wage_contribution
    urban_t, boundary_adjustment = clamp_with_adjustment(
        raw, u, state.urbanization_capacity
    )

    causes = [
        ("logistic_base_migration", base_contribution),
        ("wage_differential_pull", wage_contribution),
    ]
    if boundary_adjustment:
        causes.append(("capacity_clamp", boundary_adjustment))

    return UrbanizationUpdate(
        urban_pop_pct=urban_t,
        delta=urban_t - u,
        causes=causes,
    )
