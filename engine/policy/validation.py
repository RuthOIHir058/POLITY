"""Layer 2 policy validation and deterministic expenditure accounting."""

from __future__ import annotations

from engine.core.constants import (
    POLICY_EXPENDITURE_MAX,
    POLICY_EXPENDITURE_MIN,
    POLICY_INFLATION_TARGET_MAX,
    POLICY_INFLATION_TARGET_MIN,
    POLICY_SHARE_MAX,
    POLICY_SHARE_MIN,
    POLICY_SHARE_SUM_TOLERANCE,
    POLICY_TAX_RATE_MAX,
    POLICY_TAX_RATE_MIN,
    POLICY_TRADE_MAX,
    POLICY_TRADE_MIN,
)
from engine.core.policy_inputs import PolicyInputs


def validate_policy(policy: PolicyInputs) -> list[str]:
    """Validate every declared V1 policy range.

    Returns an empty list for a valid policy and raises one aggregated
    ``ValueError`` for invalid policy input, matching the guidebook contract.
    """

    errors: list[str] = []
    shares = policy.expenditure_shares
    share_sum = sum(shares.values())

    if abs(share_sum - 1.0) > POLICY_SHARE_SUM_TOLERANCE:
        errors.append(f"Expenditure shares sum to {share_sum:.3f}, must equal 1.0")

    for name, value in shares.items():
        if not POLICY_SHARE_MIN <= value <= POLICY_SHARE_MAX:
            errors.append(f"{name} must be between 0 and 1")

    if not POLICY_TAX_RATE_MIN <= policy.tax_rate <= POLICY_TAX_RATE_MAX:
        errors.append("Tax rate must be 5%-55% of GDP")

    if not POLICY_EXPENDITURE_MIN <= policy.total_expenditure_gdp <= POLICY_EXPENDITURE_MAX:
        errors.append("Total expenditure must be 10%-65% of GDP")

    if not POLICY_INFLATION_TARGET_MIN <= policy.inflation_target <= POLICY_INFLATION_TARGET_MAX:
        errors.append("Inflation target must be between -5% and 200%")

    if not POLICY_TRADE_MIN <= policy.trade_policy <= POLICY_TRADE_MAX:
        errors.append("Trade policy must be between -1 and 1")

    if errors:
        raise ValueError("\n".join(errors))
    return []


def expenditure_breakdown(policy: PolicyInputs) -> dict[str, float]:
    """Return all expenditure buckets as fractions of GDP."""

    total = policy.total_expenditure_gdp
    return {
        "health_spend": policy.health_share * total,
        "education_spend": policy.education_share * total,
        "infra_spend": policy.infrastructure_share * total,
        "transfers_spend": policy.social_transfers_share * total,
        "admin_spend": policy.admin_share * total,
        "military_spend": policy.military_share * total,
    }
