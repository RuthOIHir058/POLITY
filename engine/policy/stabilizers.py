"""Step-23 automatic stabilizers for extreme sovereign/labour conditions."""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.core.constants import (
    DEBT_CRITICAL_THRESHOLD,
    MIN_TRANSFER_GDP,
    NON_ESSENTIAL_BUCKET_ORDER,
    POLICY_EXPENDITURE_MIN,
    SOVEREIGN_CONSOLIDATION_BASE,
    SOVEREIGN_CONSOLIDATION_SCALE,
    UNEMPLOYMENT_SAFETY_NET_TRIGGER,
)
from engine.core.policy_inputs import PolicyInputs


@dataclass(frozen=True)
class StabilizerResult:
    policy: PolicyInputs
    sovereign_triggered: bool = False
    safety_net_triggered: bool = False
    sovereign_consolidation: float = 0.0
    safety_net_reallocation: float = 0.0
    reallocation_sources: tuple[tuple[str, float], ...] = field(default_factory=tuple)

    @property
    def triggered(self) -> bool:
        return self.sovereign_triggered or self.safety_net_triggered

    @property
    def causes(self) -> list[tuple[str, float]]:
        causes: list[tuple[str, float]] = []
        if self.sovereign_consolidation:
            causes.append(
                ("sovereign_pressure_constraint", -self.sovereign_consolidation)
            )
        if self.safety_net_reallocation:
            causes.append(("unemployment_safety_net", self.safety_net_reallocation))
        return causes


def apply_automatic_stabilizers(
    policy: PolicyInputs,
    debt_gdp_t: float,
    unemployment_t: float,
) -> StabilizerResult:
    """Return the effective policy implied by Step 23.

    The guidebook places stabilizers after the ordinary candidate path. The
    caller therefore evaluates this function on candidate end-of-year values
    and performs at most one deterministic recomputation when ``triggered``.
    """

    effective = policy
    sovereign_triggered = debt_gdp_t > DEBT_CRITICAL_THRESHOLD
    sovereign_consolidation = 0.0

    if sovereign_triggered:
        requested = (
            SOVEREIGN_CONSOLIDATION_BASE
            * (debt_gdp_t - DEBT_CRITICAL_THRESHOLD)
            * SOVEREIGN_CONSOLIDATION_SCALE
        )
        new_total = max(
            POLICY_EXPENDITURE_MIN,
            effective.total_expenditure_gdp - requested,
        )
        sovereign_consolidation = (
            effective.total_expenditure_gdp - new_total
        )
        effective = effective.with_updates(total_expenditure_gdp=new_total)

    safety_net_reallocation = 0.0
    safety_net_triggered = False
    sources: list[tuple[str, float]] = []

    transfer_spend = (
        effective.social_transfers_share * effective.total_expenditure_gdp
    )
    if (
        unemployment_t > UNEMPLOYMENT_SAFETY_NET_TRIGGER
        and transfer_spend < MIN_TRANSFER_GDP
    ):
        safety_net_triggered = True
        remaining = MIN_TRANSFER_GDP - transfer_spend
        shares = effective.expenditure_shares
        total = effective.total_expenditure_gdp
        fixed_order = {
            name: index for index, name in enumerate(NON_ESSENTIAL_BUCKET_ORDER)
        }

        ranked = sorted(
            NON_ESSENTIAL_BUCKET_ORDER,
            key=lambda name: (-shares[name] * total, fixed_order[name]),
        )
        for source in ranked:
            available = shares[source] * total
            moved = min(remaining, available)
            if moved <= 0.0:
                continue
            shares[source] -= moved / total
            shares["social_transfers_share"] += moved / total
            sources.append((source, moved))
            safety_net_reallocation += moved
            remaining -= moved
            if remaining <= 1e-15:
                break

        effective = effective.with_updates(**shares)

    return StabilizerResult(
        policy=effective,
        sovereign_triggered=sovereign_triggered,
        safety_net_triggered=safety_net_triggered,
        sovereign_consolidation=sovereign_consolidation,
        safety_net_reallocation=safety_net_reallocation,
        reallocation_sources=tuple(sources),
    )
