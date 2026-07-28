"""Authoritative constants for the deterministic POLITY V1 engine.

Every model coefficient is centralized here so equations remain auditable and
country-specific calibration values remain visibly separate from global V1
parameters.
"""

# ---------------------------------------------------------------------------
# State bounds and calibration defaults
# ---------------------------------------------------------------------------
INFLATION_MIN = -0.05
INFLATION_MAX = 2.00
UNEMPLOYMENT_MIN = 0.00
UNEMPLOYMENT_MAX = 0.40
DEBT_GDP_MIN = 0.00
DEBT_GDP_MAX = 3.00
RISK_PREMIUM_MIN = 0.00
RISK_PREMIUM_MAX = 0.25
CAPACITY_MIN = 0.05
CAPACITY_MAX = 0.95
CORRUPTION_STATE_MIN = 0.00
CORRUPTION_STATE_MAX = 1.00
CORRUPTION_MIN = 0.02  # Annual update and initialization floor
CORRUPTION_MAX = 0.98  # Annual update and initialization ceiling
YOUTH_SHARE_MIN = 0.10
YOUTH_SHARE_MAX = 0.52
WORKING_AGE_SHARE_MIN = 0.40
WORKING_AGE_SHARE_MAX = 0.80
ELDERLY_SHARE_MIN = 0.03
ELDERLY_SHARE_MAX = 0.35
HUMAN_CAPITAL_MIN = 0.00
HUMAN_CAPITAL_MAX = 1.00
LIFE_EXPECTANCY_MIN = 30.0
LIFE_EXPECTANCY_MAX = 88.0  # Tier-1 registry bound
LIFE_EXPECTANCY_UPDATE_MAX = 87.0  # Section 5.14 annual clamp
GINI_MIN = 0.20
GINI_MAX = 0.70
TRADE_OPENNESS_MIN = 0.00
TRADE_OPENNESS_MAX = 2.00
CONFLICT_RISK_MIN = 0.00
CONFLICT_RISK_MAX = 1.00

DEFAULT_POTENTIAL_GROWTH = 0.025
DEFAULT_STRUCTURAL_UNEMPLOYMENT = 0.05
DEFAULT_URBANIZATION_CAPACITY = 0.88
DEFAULT_CONFLICT_INTERCEPT = -1.5

# ---------------------------------------------------------------------------
# Policy validation
# ---------------------------------------------------------------------------
POLICY_TAX_RATE_MIN = 0.05
POLICY_TAX_RATE_MAX = 0.55
POLICY_EXPENDITURE_MIN = 0.10
POLICY_EXPENDITURE_MAX = 0.65
POLICY_SHARE_SUM_TOLERANCE = 0.001
POLICY_SHARE_MIN = 0.0
POLICY_SHARE_MAX = 1.0
POLICY_TRADE_MIN = -1.0
POLICY_TRADE_MAX = 1.0
POLICY_INFLATION_TARGET_MIN = INFLATION_MIN
POLICY_INFLATION_TARGET_MAX = INFLATION_MAX

# ---------------------------------------------------------------------------
# Demographics
# ---------------------------------------------------------------------------
DEMOGRAPHIC_LE_REFERENCE = 65.0
DEMOGRAPHIC_HC_REFERENCE = 0.5
YOUTH_LE_FERTILITY_COEFF = -0.0008
YOUTH_EDUCATION_FERTILITY_COEFF = -0.0015
ELDERLY_LE_COEFF = 0.0012
POPULATION_BIRTHS_PROXY_COEFF = 0.045

# ---------------------------------------------------------------------------
# Urbanization
# ---------------------------------------------------------------------------
URBANIZATION_K = 0.03
URBANIZATION_WAGE_GAP_MULTIPLIER = 10.0
URBANIZATION_CAPACITY_INCREMENT = 0.20
URBANIZATION_CAPACITY_MAX = 0.95

# ---------------------------------------------------------------------------
# Human-capital pipeline
# ---------------------------------------------------------------------------
HC_PIPELINE_LAG = 15
HC_DEPRECIATION = 0.003
HC_SPEND_REFERENCE = 0.05
HC_BASE_INVESTMENT = 0.002
HC_DIMINISHING_RETURN_COEFF = 0.60
DEFAULT_EDUCATION_SPEND_GDP = 0.04

# ---------------------------------------------------------------------------
# Production function (MRW delta model)
# ---------------------------------------------------------------------------
ALPHA = 0.33
BETA = 0.33
DEPRECIATION_RATE = 0.05
CAPACITY_GDP_COEFF = 0.03
DEBT_STABILITY_THRESHOLD = 0.60
DEBT_CRITICAL_THRESHOLD = 0.90
DEBT_DRAG_COEFF = 0.02
HC_TRADE_THRESHOLD = 0.40
TRADE_GDP_COEFF = 0.10

# Conflict penalty bands applied to next-year GDP growth
CONFLICT_STABLE_MAX = 0.30
CONFLICT_STRESSED_MAX = 0.50
CONFLICT_UNSTABLE_MAX = 0.70
CONFLICT_STRESSED_GDP_ADJ = -0.005
CONFLICT_UNSTABLE_GDP_ADJ = -0.015
CONFLICT_CRISIS_BASE_GDP_ADJ = -0.030
CONFLICT_CRISIS_SLOPE = -0.020

# ---------------------------------------------------------------------------
# Output gap and inflation (Hybrid NKPC)
# ---------------------------------------------------------------------------
OUTPUT_GAP_MIN = -0.30
OUTPUT_GAP_MAX = 0.30
OUTPUT_GAP_DENOMINATOR_FLOOR = 0.001
INFLATION_PERSISTENCE = 0.50
INFLATION_UNMODELLED_WEIGHT = 0.20
NKPC_KAPPA = 0.08
PASSTHROUGH_RATE = 0.30

# ---------------------------------------------------------------------------
# Unemployment
# ---------------------------------------------------------------------------
OKUN_COEFFICIENT = 0.40

# ---------------------------------------------------------------------------
# Debt and sovereign risk
# ---------------------------------------------------------------------------
RISK_FREE_RATE = 0.02
RP_AUTOREGRESSION = 0.85
DEBT_RISK_LOW_THRESHOLD = 0.40
DEBT_RISK_MID_THRESHOLD = 0.60
DEBT_RISK_HIGH_THRESHOLD = 0.90
DEBT_RISK_LOW_MAX = 0.005
DEBT_RISK_HIGH_MAX = 0.045
DEBT_RISK_EXPONENTIAL_COEFF = 0.10

# ---------------------------------------------------------------------------
# Gini
# ---------------------------------------------------------------------------
GINI_PERSISTENCE = 0.90
GINI_INFLATION_THRESHOLD = 0.05
GINI_INFLATION_COEFF = 0.005
GINI_UNEMPLOYMENT_COEFF = 0.003
GINI_HC_REFERENCE = 0.5
GINI_HC_COEFF = -0.008
GINI_TRADE_THRESHOLD = 0.80
GINI_TRADE_COEFF = 0.002
GINI_TRANSFER_THRESHOLD = 0.05
GINI_TRANSFER_COEFF = -0.010

# ---------------------------------------------------------------------------
# Life expectancy (Preston curve delta)
# ---------------------------------------------------------------------------
LE_HEALTH_LOG_COEFF = 0.30
LE_HEALTH_SPEND_SCALE = 100.0
LE_EDUCATION_COEFF = 0.15
LE_HC_REFERENCE = 0.5
LE_INCOME_LOG_COEFF = 2.0
LE_INCOME_EFFECT_MIN = -1.0
LE_INCOME_EFFECT_MAX = 1.0
LE_CEILING_BASE = 60.0
LE_CEILING_LOG_COEFF = 18.0
LE_CEILING_INCOME_SCALE = 1000.0
LE_CEILING_INCOME_FLOOR = 0.1
LE_CEILING_MIN = 45.0
LE_CEILING_MAX = 87.0
LE_ADJUSTMENT_SPEED = 0.30
LE_INCOME_FINAL_WEIGHT = 0.10

# ---------------------------------------------------------------------------
# School life expectancy and reference metrics
# ---------------------------------------------------------------------------
SLE_HC_YEARS_MAX = 18.0
SLE_SPENDING_COEFF = 2.0
SLE_SPENDING_REFERENCE = 0.04
SLE_MIN = 4.0
SLE_MAX = 20.0
MYS_MAX = 15.0
EYS_MAX = 18.0
HDI_LE_MIN = 20.0
HDI_LE_MAX = 85.0
HDI_INCOME_MIN = 100.0
HDI_INCOME_MAX = 75_000.0

# ---------------------------------------------------------------------------
# State capacity
# ---------------------------------------------------------------------------
FISCAL_CAPACITY_REVENUE_REFERENCE = 0.40
FISCAL_ADMIN_INVEST_COEFF = 0.020
LEGAL_ADMIN_INVEST_COEFF = 0.015
ADMIN_SPEND_REFERENCE = 0.02
CAPACITY_NATURAL_DECAY = 0.010
CAPACITY_CORRUPTION_DRAG_F = 0.025
CAPACITY_CORRUPTION_DRAG_L = 0.030
CAPACITY_CONFLICT_DEGRADE_F = 0.050
CAPACITY_CONFLICT_DEGRADE_L = 0.080
CAPACITY_STRESSED_INVESTMENT_FACTOR = 0.50
CAPACITY_BLOCKED_INVESTMENT_FACTOR = 0.0

# ---------------------------------------------------------------------------
# Corruption
# ---------------------------------------------------------------------------
CORRUPTION_LEGAL_REDUCTION_COEFF = 0.020
CORRUPTION_CONFLICT_THRESHOLD = 0.40
CORRUPTION_CONFLICT_PUSH_COEFF = 0.030
CORRUPTION_POVERTY_REFERENCE = 0.50
CORRUPTION_POVERTY_INCOME_SCALE = 20_000.0
CORRUPTION_POVERTY_PUSH_COEFF = 0.010

# ---------------------------------------------------------------------------
# Political stability logistic model
# ---------------------------------------------------------------------------
CONFLICT_YOUTH_CENTER = 0.15
CONFLICT_YOUTH_SCALE = 0.20
CONFLICT_UNEMPLOYMENT_BUFFER = 0.03
CONFLICT_GINI_THRESHOLD = 0.40
CONFLICT_INFLATION_THRESHOLD = 0.10
CONFLICT_YOUTH_COEFF = 0.80
CONFLICT_UNEMP_COEFF = 0.50
CONFLICT_URBAN_COEFF = 0.60
CONFLICT_GINI_COEFF = 0.70
CONFLICT_RECESSION_COEFF = 0.60
CONFLICT_INFLATION_COEFF = 0.40
CONFLICT_CAPACITY_PROTECT = 0.50
CONFLICT_MILITARY_SUPPRESS = 0.30
CONFLICT_CALIBRATION_MIN = 0.01
CONFLICT_CALIBRATION_MAX = 0.99

# ---------------------------------------------------------------------------
# Trade policy
# ---------------------------------------------------------------------------
TRADE_POLICY_TARGET_COEFF = 0.30
TRADE_CONVERGENCE_RATE = 0.20

# ---------------------------------------------------------------------------
# Automatic stabilizers
# ---------------------------------------------------------------------------
SOVEREIGN_CONSOLIDATION_BASE = 0.005
SOVEREIGN_CONSOLIDATION_SCALE = 10.0
UNEMPLOYMENT_SAFETY_NET_TRIGGER = 0.20
MIN_TRANSFER_GDP = 0.01
NON_ESSENTIAL_BUCKET_ORDER = (
    "infrastructure_share",
    "admin_share",
    "military_share",
)

# ---------------------------------------------------------------------------
# Explainability severity thresholds
# ---------------------------------------------------------------------------
SEVERITY_THRESHOLDS: dict[str, tuple[float, float, float]] = {
    "gdp_growth": (0.010, 0.030, 0.060),
    "inflation": (0.020, 0.050, 0.150),
    "unemployment": (0.010, 0.025, 0.050),
    "debt_gdp": (0.030, 0.080, 0.150),
    "conflict_risk": (0.050, 0.120, 0.250),
    "fiscal_capacity": (0.020, 0.050, 0.100),
    "legal_capacity": (0.020, 0.050, 0.100),
    "human_capital": (0.005, 0.015, 0.030),
    "life_expectancy": (0.500, 1.500, 3.000),
    "gini": (0.005, 0.020, 0.050),
}


def classify_severity(variable: str, abs_delta: float) -> str:
    """Classify an absolute change using the guidebook thresholds."""

    thresholds = SEVERITY_THRESHOLDS.get(variable, (0.01, 0.05, 0.10))
    if abs_delta < thresholds[0]:
        return "none"
    if abs_delta < thresholds[1]:
        return "notable"
    if abs_delta < thresholds[2]:
        return "significant"
    return "critical"
