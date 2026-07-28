"""Layer 3 Besley-Persson state-capacity and corruption updates."""

from __future__ import annotations

from dataclasses import dataclass

from engine.core.constants import (
    ADMIN_SPEND_REFERENCE,
    CAPACITY_BLOCKED_INVESTMENT_FACTOR,
    CAPACITY_CONFLICT_DEGRADE_F,
    CAPACITY_CONFLICT_DEGRADE_L,
    CAPACITY_CORRUPTION_DRAG_F,
    CAPACITY_CORRUPTION_DRAG_L,
    CAPACITY_MAX,
    CAPACITY_MIN,
    CAPACITY_NATURAL_DECAY,
    CAPACITY_STRESSED_INVESTMENT_FACTOR,
    CONFLICT_STABLE_MAX,
    CONFLICT_STRESSED_MAX,
    CORRUPTION_CONFLICT_PUSH_COEFF,
    CORRUPTION_CONFLICT_THRESHOLD,
    CORRUPTION_LEGAL_REDUCTION_COEFF,
    CORRUPTION_MAX,
    CORRUPTION_MIN,
    CORRUPTION_POVERTY_INCOME_SCALE,
    CORRUPTION_POVERTY_PUSH_COEFF,
    CORRUPTION_POVERTY_REFERENCE,
    FISCAL_ADMIN_INVEST_COEFF,
    LEGAL_ADMIN_INVEST_COEFF,
)
from engine.core.country_state import CountryState
from engine.core.helpers import clamp_with_adjustment


@dataclass(frozen=True)
class CapacityUpdate:
    fiscal_capacity: float
    legal_capacity: float
    investment_factor: float
    fiscal_causes: list[tuple[str, float]]
    legal_causes: list[tuple[str, float]]


@dataclass(frozen=True)
class CorruptionUpdate:
    corruption: float
    causes: list[tuple[str, float]]


def capacity_investment_factor(conflict_risk: float) -> float:
    if conflict_risk < CONFLICT_STABLE_MAX:
        return 1.0
    if conflict_risk < CONFLICT_STRESSED_MAX:
        return CAPACITY_STRESSED_INVESTMENT_FACTOR
    return CAPACITY_BLOCKED_INVESTMENT_FACTOR


def update_state_capacity(
    state: CountryState,
    admin_spend: float,
) -> CapacityUpdate:
    factor = capacity_investment_factor(state.conflict_risk)

    fiscal_investment = (
        FISCAL_ADMIN_INVEST_COEFF
        * (admin_spend / ADMIN_SPEND_REFERENCE)
        * factor
    )
    fiscal_corruption_drag = -CAPACITY_CORRUPTION_DRAG_F * state.corruption
    fiscal_decay = -CAPACITY_NATURAL_DECAY
    fiscal_conflict = (
        -CAPACITY_CONFLICT_DEGRADE_F
        if state.conflict_risk > CONFLICT_STRESSED_MAX
        else 0.0
    )
    raw_fiscal = state.fiscal_capacity + (
        fiscal_investment
        + fiscal_corruption_drag
        + fiscal_decay
        + fiscal_conflict
    )
    fiscal_t, fiscal_boundary = clamp_with_adjustment(
        raw_fiscal, CAPACITY_MIN, CAPACITY_MAX
    )

    legal_investment = (
        LEGAL_ADMIN_INVEST_COEFF
        * (admin_spend / ADMIN_SPEND_REFERENCE)
        * factor
    )
    legal_corruption_drag = -CAPACITY_CORRUPTION_DRAG_L * state.corruption
    legal_decay = -CAPACITY_NATURAL_DECAY
    legal_conflict = (
        -CAPACITY_CONFLICT_DEGRADE_L
        if state.conflict_risk > CONFLICT_STRESSED_MAX
        else 0.0
    )
    raw_legal = state.legal_capacity + (
        legal_investment
        + legal_corruption_drag
        + legal_decay
        + legal_conflict
    )
    legal_t, legal_boundary = clamp_with_adjustment(
        raw_legal, CAPACITY_MIN, CAPACITY_MAX
    )

    fiscal_causes = [
        ("admin_investment", fiscal_investment),
        ("corruption_drag", fiscal_corruption_drag),
        ("natural_decay", fiscal_decay),
        ("conflict_degradation", fiscal_conflict),
    ]
    legal_causes = [
        ("admin_investment", legal_investment),
        ("corruption_drag", legal_corruption_drag),
        ("natural_decay", legal_decay),
        ("conflict_degradation", legal_conflict),
    ]
    if fiscal_boundary:
        fiscal_causes.append(("range_clamp", fiscal_boundary))
    if legal_boundary:
        legal_causes.append(("range_clamp", legal_boundary))

    return CapacityUpdate(
        fiscal_capacity=fiscal_t,
        legal_capacity=legal_t,
        investment_factor=factor,
        fiscal_causes=fiscal_causes,
        legal_causes=legal_causes,
    )


def update_corruption(
    state: CountryState,
    gdp_per_capita_t: float,
) -> CorruptionUpdate:
    legal_reduction = -CORRUPTION_LEGAL_REDUCTION_COEFF * state.legal_capacity
    conflict_push = CORRUPTION_CONFLICT_PUSH_COEFF * max(
        0.0, state.conflict_risk - CORRUPTION_CONFLICT_THRESHOLD
    )
    poverty_push = CORRUPTION_POVERTY_PUSH_COEFF * max(
        0.0,
        CORRUPTION_POVERTY_REFERENCE
        - gdp_per_capita_t / CORRUPTION_POVERTY_INCOME_SCALE,
    )

    raw = state.corruption + conflict_push + poverty_push + legal_reduction
    corruption_t, boundary_adjustment = clamp_with_adjustment(
        raw, CORRUPTION_MIN, CORRUPTION_MAX
    )
    causes = [
        ("conflict_push", conflict_push),
        ("poverty_push", poverty_push),
        ("legal_capacity_suppression", legal_reduction),
    ]
    if boundary_adjustment:
        causes.append(("range_clamp", boundary_adjustment))

    return CorruptionUpdate(corruption=corruption_t, causes=causes)
