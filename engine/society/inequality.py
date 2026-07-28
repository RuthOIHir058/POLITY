"""Layer 5 persistent Gini update with named structural drivers."""

from __future__ import annotations

from dataclasses import dataclass

from engine.core.constants import (
    GINI_HC_COEFF,
    GINI_HC_REFERENCE,
    GINI_INFLATION_COEFF,
    GINI_INFLATION_THRESHOLD,
    GINI_MAX,
    GINI_MIN,
    GINI_PERSISTENCE,
    GINI_TRADE_COEFF,
    GINI_TRADE_THRESHOLD,
    GINI_TRANSFER_COEFF,
    GINI_TRANSFER_THRESHOLD,
    GINI_UNEMPLOYMENT_COEFF,
)
from engine.core.country_state import CountryState
from engine.core.helpers import clamp_with_adjustment


@dataclass(frozen=True)
class GiniUpdate:
    gini: float
    structural_target: float
    raw_drivers: dict[str, float]
    causes: list[tuple[str, float]]


def update_gini(
    state: CountryState,
    inflation_t: float,
    unemployment_t: float,
    transfers_spend: float,
) -> GiniUpdate:
    raw_drivers = {
        "inflation_inequality": GINI_INFLATION_COEFF
        * max(0.0, inflation_t - GINI_INFLATION_THRESHOLD),
        "unemployment_inequality": GINI_UNEMPLOYMENT_COEFF
        * max(0.0, unemployment_t - state.structural_unemployment),
        "human_capital_equalization": GINI_HC_COEFF
        * (state.human_capital - GINI_HC_REFERENCE),
        "trade_skill_premium": GINI_TRADE_COEFF
        * max(0.0, state.trade_openness - GINI_TRADE_THRESHOLD),
        "social_transfers": GINI_TRANSFER_COEFF
        * max(0.0, transfers_spend - GINI_TRANSFER_THRESHOLD),
    }
    structural = state.gini + sum(raw_drivers.values())
    raw_gini = (
        GINI_PERSISTENCE * state.gini
        + (1.0 - GINI_PERSISTENCE) * structural
    )
    gini_t, boundary_adjustment = clamp_with_adjustment(
        raw_gini, GINI_MIN, GINI_MAX
    )

    weight = 1.0 - GINI_PERSISTENCE
    causes = [(name, weight * value) for name, value in raw_drivers.items()]
    if boundary_adjustment:
        causes.append(("range_clamp", boundary_adjustment))

    return GiniUpdate(
        gini=gini_t,
        structural_target=structural,
        raw_drivers=raw_drivers,
        causes=causes,
    )
