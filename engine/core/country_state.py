"""Canonical persisted country state for the POLITY V1 simulation."""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field

from engine.core.constants import (
    CONFLICT_RISK_MAX,
    CONFLICT_RISK_MIN,
    CORRUPTION_STATE_MAX,
    CORRUPTION_STATE_MIN,
    DEBT_GDP_MAX,
    DEBT_GDP_MIN,
    DEFAULT_CONFLICT_INTERCEPT,
    DEFAULT_POTENTIAL_GROWTH,
    DEFAULT_STRUCTURAL_UNEMPLOYMENT,
    DEFAULT_URBANIZATION_CAPACITY,
    GINI_MAX,
    GINI_MIN,
    HC_PIPELINE_LAG,
    HUMAN_CAPITAL_MAX,
    HUMAN_CAPITAL_MIN,
    INFLATION_MAX,
    INFLATION_MIN,
    LIFE_EXPECTANCY_MAX,
    LIFE_EXPECTANCY_MIN,
    RISK_PREMIUM_MAX,
    RISK_PREMIUM_MIN,
    TRADE_OPENNESS_MAX,
    TRADE_OPENNESS_MIN,
    UNEMPLOYMENT_MAX,
    UNEMPLOYMENT_MIN,
)
from engine.core.helpers import finite_float


@dataclass
class CountryState:
    # Identifiers
    country_code: str
    year: int

    # Economy (Tier 1)
    gdp: float
    inflation: float
    unemployment: float
    debt_gdp: float
    risk_premium: float

    # Governance (Tier 1)
    fiscal_capacity: float
    legal_capacity: float
    corruption: float

    # Demographics (Tier 1)
    population: float
    youth_share: float
    working_age_share: float
    elderly_share: float
    urban_pop_pct: float

    # Society (Tier 1)
    human_capital: float
    life_expectancy: float
    gini: float
    trade_openness: float

    # Political stability is required by the next-year GDP/capacity equations.
    conflict_risk: float = 0.0

    # Internal simulation state
    hc_pipeline: deque[float] = field(
        default_factory=lambda: deque([0.0] * HC_PIPELINE_LAG, maxlen=HC_PIPELINE_LAG)
    )

    # Country-specific calibration constants (never updated by step())
    potential_growth: float = DEFAULT_POTENTIAL_GROWTH
    structural_unemployment: float = DEFAULT_STRUCTURAL_UNEMPLOYMENT
    urbanization_capacity: float = DEFAULT_URBANIZATION_CAPACITY
    conflict_intercept: float = DEFAULT_CONFLICT_INTERCEPT

    # Section 5.3 requires prior-year growth for urbanization. It is internal,
    # not a player-facing Tier-2 registry value.
    previous_gdp_growth: float | None = None

    def __post_init__(self) -> None:
        self.country_code = str(self.country_code).upper().strip()
        if not self.country_code:
            raise ValueError("country_code must not be empty")
        if not isinstance(self.year, int):
            raise ValueError("year must be an integer")

        numeric_fields = (
            "gdp",
            "inflation",
            "unemployment",
            "debt_gdp",
            "risk_premium",
            "fiscal_capacity",
            "legal_capacity",
            "corruption",
            "population",
            "youth_share",
            "working_age_share",
            "elderly_share",
            "urban_pop_pct",
            "human_capital",
            "life_expectancy",
            "gini",
            "trade_openness",
            "conflict_risk",
            "potential_growth",
            "structural_unemployment",
            "urbanization_capacity",
            "conflict_intercept",
        )
        for name in numeric_fields:
            setattr(self, name, finite_float(getattr(self, name), name))

        if self.previous_gdp_growth is None:
            self.previous_gdp_growth = self.potential_growth
        else:
            self.previous_gdp_growth = finite_float(
                self.previous_gdp_growth, "previous_gdp_growth"
            )

        self.hc_pipeline = deque(
            (finite_float(value, "hc_pipeline item") for value in self.hc_pipeline),
            maxlen=HC_PIPELINE_LAG,
        )
        if len(self.hc_pipeline) != HC_PIPELINE_LAG:
            raise ValueError(
                f"hc_pipeline must contain exactly {HC_PIPELINE_LAG} investments"
            )

        self.validate_ranges()

    def validate_ranges(self) -> None:
        """Validate the state registry bounds without changing the state."""

        checks = {
            "inflation": (self.inflation, INFLATION_MIN, INFLATION_MAX),
            "unemployment": (
                self.unemployment,
                UNEMPLOYMENT_MIN,
                UNEMPLOYMENT_MAX,
            ),
            "debt_gdp": (self.debt_gdp, DEBT_GDP_MIN, DEBT_GDP_MAX),
            "risk_premium": (
                self.risk_premium,
                RISK_PREMIUM_MIN,
                RISK_PREMIUM_MAX,
            ),
            "fiscal_capacity": (self.fiscal_capacity, 0.0, 1.0),
            "legal_capacity": (self.legal_capacity, 0.0, 1.0),
            "corruption": (
                self.corruption,
                CORRUPTION_STATE_MIN,
                CORRUPTION_STATE_MAX,
            ),
            "youth_share": (self.youth_share, 0.0, 1.0),
            "working_age_share": (self.working_age_share, 0.0, 1.0),
            "elderly_share": (self.elderly_share, 0.0, 1.0),
            "urban_pop_pct": (self.urban_pop_pct, 0.0, 1.0),
            "human_capital": (
                self.human_capital,
                HUMAN_CAPITAL_MIN,
                HUMAN_CAPITAL_MAX,
            ),
            "life_expectancy": (
                self.life_expectancy,
                LIFE_EXPECTANCY_MIN,
                LIFE_EXPECTANCY_MAX,
            ),
            "gini": (self.gini, GINI_MIN, GINI_MAX),
            "trade_openness": (
                self.trade_openness,
                TRADE_OPENNESS_MIN,
                TRADE_OPENNESS_MAX,
            ),
            "conflict_risk": (
                self.conflict_risk,
                CONFLICT_RISK_MIN,
                CONFLICT_RISK_MAX,
            ),
            "structural_unemployment": (
                self.structural_unemployment,
                UNEMPLOYMENT_MIN,
                UNEMPLOYMENT_MAX,
            ),
            "urbanization_capacity": (self.urbanization_capacity, 0.0, 1.0),
        }
        for name, (value, lo, hi) in checks.items():
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside [{lo}, {hi}]")

        if self.gdp <= 0.0:
            raise ValueError("gdp must be greater than zero")
        if self.population <= 0.0:
            raise ValueError("population must be greater than zero")
        if self.urban_pop_pct > self.urbanization_capacity + 1e-12:
            raise ValueError(
                "urban_pop_pct cannot exceed the calibrated urbanization_capacity"
            )

    def clone(self) -> "CountryState":
        """Return a deep copy suitable for deterministic step calculations."""

        return deepcopy(self)
