"""Player/AI policy inputs for one deterministic annual step."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class PolicyInputs:
    # Fiscal
    tax_rate: float = 0.25
    total_expenditure_gdp: float = 0.30

    # Expenditure breakdown — must sum to 1.0
    health_share: float = 0.15
    education_share: float = 0.15
    infrastructure_share: float = 0.15
    social_transfers_share: float = 0.20
    admin_share: float = 0.20
    military_share: float = 0.15

    # Monetary
    inflation_target: float = 0.02

    # Structural
    trade_policy: float = 0.0

    @property
    def expenditure_shares(self) -> dict[str, float]:
        return {
            "health_share": self.health_share,
            "education_share": self.education_share,
            "infrastructure_share": self.infrastructure_share,
            "social_transfers_share": self.social_transfers_share,
            "admin_share": self.admin_share,
            "military_share": self.military_share,
        }

    def with_updates(self, **updates: float) -> "PolicyInputs":
        """Return a new immutable policy with deterministic field updates."""

        return replace(self, **updates)
