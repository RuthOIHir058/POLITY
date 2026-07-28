"""Layer 4 domestic trade-openness adjustment for POLITY V1."""

from __future__ import annotations

from dataclasses import dataclass

from engine.core.constants import (
    TRADE_CONVERGENCE_RATE,
    TRADE_OPENNESS_MAX,
    TRADE_OPENNESS_MIN,
    TRADE_POLICY_TARGET_COEFF,
)
from engine.core.country_state import CountryState
from engine.core.helpers import clamp_with_adjustment
from engine.core.policy_inputs import PolicyInputs


@dataclass(frozen=True)
class TradeUpdate:
    trade_openness: float
    target: float
    delta: float
    causes: list[tuple[str, float]]


def update_trade_openness(
    state: CountryState,
    policy: PolicyInputs,
) -> TradeUpdate:
    target = state.trade_openness * (
        1.0 + TRADE_POLICY_TARGET_COEFF * policy.trade_policy
    )
    convergence = TRADE_CONVERGENCE_RATE * (
        target - state.trade_openness
    )
    raw = state.trade_openness + convergence
    trade_t, boundary_adjustment = clamp_with_adjustment(
        raw, TRADE_OPENNESS_MIN, TRADE_OPENNESS_MAX
    )

    causes = [("policy_target_convergence", convergence)]
    if boundary_adjustment:
        causes.append(("range_clamp", boundary_adjustment))

    return TradeUpdate(
        trade_openness=trade_t,
        target=target,
        delta=trade_t - state.trade_openness,
        causes=causes,
    )
