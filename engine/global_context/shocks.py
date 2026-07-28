"""Layer 1 deterministic external context inputs for POLITY V1.

V1 contains no random shock generator. Callers may supply an explicit import
price change; omission is exactly zero and therefore deterministic.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from engine.core.helpers import finite_float


@dataclass(frozen=True)
class ExternalShocks:
    import_price_change: float = 0.0


def normalize_external_shocks(
    shocks: ExternalShocks | Mapping[str, float] | None,
) -> ExternalShocks:
    if shocks is None:
        return ExternalShocks()
    if isinstance(shocks, ExternalShocks):
        return shocks
    return ExternalShocks(
        import_price_change=finite_float(
            shocks.get("import_price_change", 0.0), "import_price_change"
        )
    )
