"""Authoritative POLITY V1 variable registry."""

TIER1_VARIABLES = {
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
    # Required persistence reconciliation for Sections 5.6, 6, and 8.
    "conflict_risk",
}

TIER2_VARIABLES = {
    "gdp_growth",
    "gdp_per_capita",
    "output_gap",
    "tax_revenue_gdp",
    "primary_balance_gdp",
    "conflict_risk",
    "political_stability_score",
    "school_life_expectancy",
}

TIER3_VARIABLES = {
    "hdi",
    "mean_years_schooling",
    "expected_years_schooling",
}

INTERNAL_STATE_VARIABLES = {
    "hc_pipeline",
    "previous_gdp_growth",
}

CALIBRATION_VARIABLES = {
    "potential_growth",
    "structural_unemployment",
    "urbanization_capacity",
    "conflict_intercept",
}

ALL_VARIABLES = TIER1_VARIABLES | TIER2_VARIABLES | TIER3_VARIABLES
