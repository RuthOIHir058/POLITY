"""Layer 5: demographic and social outcomes."""

from engine.society.demographics import DemographicsUpdate, update_demographics
from engine.society.health import (
    LifeExpectancyUpdate,
    SchoolLifeExpectancy,
    compute_school_life_expectancy,
    update_life_expectancy,
)
from engine.society.human_capital import (
    HumanCapitalUpdate,
    compute_hc_investment,
    initialize_hc_pipeline,
    step_human_capital,
)
from engine.society.inequality import GiniUpdate, update_gini
from engine.society.reference_metrics import (
    ReferenceMetrics,
    compute_reference_metrics,
)
from engine.society.urbanization import UrbanizationUpdate, update_urbanization

__all__ = [
    "DemographicsUpdate",
    "GiniUpdate",
    "HumanCapitalUpdate",
    "LifeExpectancyUpdate",
    "ReferenceMetrics",
    "SchoolLifeExpectancy",
    "UrbanizationUpdate",
    "compute_hc_investment",
    "compute_reference_metrics",
    "compute_school_life_expectancy",
    "initialize_hc_pipeline",
    "step_human_capital",
    "update_demographics",
    "update_gini",
    "update_life_expectancy",
    "update_urbanization",
]
