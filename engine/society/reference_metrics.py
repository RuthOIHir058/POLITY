"""Tier-3 display metrics. These functions are never read by model equations."""

from __future__ import annotations

import math
from dataclasses import dataclass

from engine.core.constants import (
    EYS_MAX,
    HDI_INCOME_MAX,
    HDI_INCOME_MIN,
    HDI_LE_MAX,
    HDI_LE_MIN,
    MYS_MAX,
)
from engine.core.helpers import clamp


@dataclass(frozen=True)
class ReferenceMetrics:
    hdi: float
    mean_years_schooling: float
    expected_years_schooling: float
    life_expectancy_index: float
    education_index: float
    income_index: float


def compute_reference_metrics(
    gdp_per_capita: float,
    life_expectancy: float,
    human_capital: float,
    school_life_expectancy: float,
) -> ReferenceMetrics:
    mean_years_schooling = human_capital * MYS_MAX
    expected_years_schooling = school_life_expectancy

    life_expectancy_index = clamp(
        (life_expectancy - HDI_LE_MIN) / (HDI_LE_MAX - HDI_LE_MIN),
        0.0,
        1.0,
    )
    education_index = (
        min(mean_years_schooling, MYS_MAX) / MYS_MAX
        + min(expected_years_schooling, EYS_MAX) / EYS_MAX
    ) / 2.0

    income_for_index = clamp(
        gdp_per_capita, HDI_INCOME_MIN, HDI_INCOME_MAX
    )
    income_index = (
        math.log(income_for_index) - math.log(HDI_INCOME_MIN)
    ) / (math.log(HDI_INCOME_MAX) - math.log(HDI_INCOME_MIN))

    hdi = (life_expectancy_index * education_index * income_index) ** (1.0 / 3.0)

    return ReferenceMetrics(
        hdi=hdi,
        mean_years_schooling=mean_years_schooling,
        expected_years_schooling=expected_years_schooling,
        life_expectancy_index=life_expectancy_index,
        education_index=education_index,
        income_index=income_index,
    )
