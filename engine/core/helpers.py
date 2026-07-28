"""Small deterministic arithmetic helpers shared by engine modules."""

from __future__ import annotations

import math
from collections.abc import Iterable


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp *value* to the closed interval [lo, hi]."""

    if lo > hi:
        raise ValueError(f"Invalid clamp bounds: {lo} > {hi}")
    return max(lo, min(hi, value))


def clamp_with_adjustment(value: float, lo: float, hi: float) -> tuple[float, float]:
    """Return the clamped value and the additive boundary adjustment."""

    clamped = clamp(value, lo, hi)
    return clamped, clamped - value


def logistic(eta: float) -> float:
    """Numerically stable logistic transform."""

    if eta >= 0.0:
        z = math.exp(-eta)
        return 1.0 / (1.0 + z)
    z = math.exp(eta)
    return z / (1.0 + z)


def trimmed_mean(values: Iterable[float], trim: float = 0.10) -> float:
    """Compute a deterministic symmetric trimmed mean.

    The guidebook's formula assumes a multi-observation historical window. For
    very short series where trimming would remove every observation, this
    implementation returns the ordinary mean rather than an artificial zero.
    """

    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("trimmed_mean requires at least one value")
    if not 0.0 <= trim < 0.5:
        raise ValueError("trim must be in [0.0, 0.5)")

    k = max(1, int(len(ordered) * trim)) if trim > 0.0 else 0
    if 2 * k >= len(ordered):
        sample = ordered
    else:
        sample = ordered[k:-k] if k else ordered
    return sum(sample) / len(sample)


def finite_float(value: object, field_name: str) -> float:
    """Convert a value to a finite float or raise a descriptive error."""

    try:
        converted = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric, got {value!r}") from exc
    if not math.isfinite(converted):
        raise ValueError(f"{field_name} must be finite, got {converted!r}")
    return converted
