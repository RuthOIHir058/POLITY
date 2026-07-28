# POLITY Engine V1 — Implementation Specification

---

## 1. Design Philosophy & Constraints

The engine must satisfy four non-negotiable properties:

- **Explainable**: Every variable change has a named cause. The audit log must answer "Why did this happen?" for any variable in any year.
- **Deterministic**: Identical initial state + identical policy → identical output. Random shocks are opt-in and deferred to V1.5.
- **Calibrated**: A country loaded at its historical baseline, given policy inputs matching its historical averages, stays on a plausible trajectory. It should not drift 50% off historical in 10 years.
- **Tractable**: No agent populations. No ML. No DSGE optimization loops. All equations are closed-form arithmetic. A solo developer can implement and debug the full engine.

**Implementation contract**: Every `step()` call returns both an updated `CountryState` and an `AuditLog` — a list of entries mapping each changed variable to its contributing causes and their magnitudes.

### Simplifications Made for V1

The following deliberate simplifications are locked in for V1. They are documented here so they are not "discovered" mid-implementation:

| Research Mechanism | V1 Simplification | Deferred To |
|---|---|---|
| Full cohort-component age array | Aggregate cohort shares (youth/working/elderly) with simple update rules | V2 |
| DSGE monetary policy model | Inflation target as a policy lever; simplified NKPC | V1.5 |
| Physical capital as tracked stock | Implicit via infrastructure spend delta | V1.5 |
| Harris-Todaro micro migration | Logistic urbanization with wage-gap proxy | V1 (sufficient) |
| MRW steady-state convergence | Delta-based growth model around potential growth | V1 (intentional) |
| Regime type constraints | No regime modelling | V2 |
| Inter-country trade | Trade openness is domestic policy lever only | V2 |
| Financial sector / credit cycle | Not modelled | V2 |

---

## 2. Variable Registry

### 2.1 Tier 1 — State Variables

Persisted between timesteps. Updated only by explicit equations inside `step()`. Never computed on-the-fly.

| Variable | Type | Range | Initialized From |
|---|---|---|---|
| `gdp` | float | > 0 (USD absolute) | Historical |
| `inflation` | float | −0.05 → 2.0 | Historical |
| `unemployment` | float | 0 → 0.40 | Historical |
| `debt_gdp` | float | 0 → 3.0 | Historical |
| `risk_premium` | float | 0 → 0.25 | Derived at init |
| `fiscal_capacity` | float | 0 → 1 | Normalized from Revenue/GDP |
| `legal_capacity` | float | 0 → 1 | Normalized from Rule of Law WGI |
| `corruption` | float | 0 → 1 | Normalized from Corruption Index WGI |
| `population` | float | > 0 | Historical |
| `youth_share` | float | 0 → 1 | Historical |
| `working_age_share` | float | 0 → 1 | Historical |
| `elderly_share` | float | 0 → 1 | Historical |
| `urban_pop_pct` | float | 0 → 1 | Historical |
| `human_capital` | float | 0 → 1 | Normalized Education Index |
| `life_expectancy` | float | 30 → 88 | Historical |
| `gini` | float | 0.20 → 0.70 | Historical |
| `trade_openness` | float | 0 → 2.0 | Historical (X+M)/GDP |
| `hc_pipeline` | deque[float] | — | Backfilled at init (see §8) |

### 2.2 Tier 2 — Derived Variables

Computed fresh each timestep from Tier 1 values. Not persisted directly, but included in the step return dict and audit log.

| Variable | Computed From |
|---|---|
| `gdp_growth` | `(gdp_t − gdp_{t−1}) / gdp_{t−1}` |
| `gdp_per_capita` | `gdp / population` |
| `output_gap` | `(gdp_growth − potential_growth) / potential_growth` |
| `tax_revenue_gdp` | `tax_rate × fiscal_capacity` |
| `primary_balance_gdp` | `tax_revenue_gdp − total_expenditure_gdp` |
| `conflict_risk` | Logistic function of demographics + economy (§8) |
| `political_stability_score` | `2.5 − (5.0 × conflict_risk)` — maps to WGI scale |
| `school_life_expectancy` | Function of education spend and human capital |

### 2.3 Tier 3 — Reference Metrics

Computed post-step for display only. **Never read back into the simulation engine.**

| Variable | Formula |
|---|---|
| `HDI` | UNDP composite of income index, education index, LE index |
| `mean_years_schooling` | `human_capital × 15.0` (inverse of normalization) |
| `expected_years_schooling` | `school_life_expectancy` expressed in years |

---

## 3. Data Structures

### 3.1 CountryState

Extend the existing `CountryState` object with all fields below. Fields marked `# CALIB` are set at initialization and never updated by `step()`.

```python
from dataclasses import dataclass, field
from collections import deque

@dataclass
class CountryState:
    # --- Identifiers ---
    country_code: str
    year: int

    # --- Economy (Tier 1) ---
    gdp: float
    inflation: float
    unemployment: float
    debt_gdp: float
    risk_premium: float

    # --- Governance (Tier 1) ---
    fiscal_capacity: float      # [0, 1]
    legal_capacity: float       # [0, 1]
    corruption: float           # [0, 1], 1 = maximally corrupt

    # --- Demographics (Tier 1) ---
    population: float
    youth_share: float          # 0–14 cohort share
    working_age_share: float    # 15–64 cohort share
    elderly_share: float        # 65+ cohort share
    urban_pop_pct: float        # [0, 1]

    # --- Society (Tier 1) ---
    human_capital: float        # [0, 1]
    life_expectancy: float
    gini: float
    trade_openness: float       # (X + M) / GDP

    # --- Internal simulation state ---
    hc_pipeline: deque = field(default_factory=lambda: deque([0.0]*15, maxlen=15))

    # --- Country-specific calibration constants (CALIB — never updated by step()) ---
    potential_growth: float = 0.025         # CALIB
    structural_unemployment: float = 0.05   # CALIB
    urbanization_capacity: float = 0.88     # CALIB — L_max for logistic
    conflict_intercept: float = -1.5        # CALIB — fitted to historical stability
```

### 3.2 PolicyInputs

```python
@dataclass
class PolicyInputs:
    # --- Fiscal ---
    tax_rate: float                  # Target revenue/GDP (e.g. 0.25 = 25%)
    total_expenditure_gdp: float     # Total spending/GDP (deficit if > tax_rate)

    # --- Expenditure breakdown — must sum to 1.0 ---
    health_share: float
    education_share: float
    infrastructure_share: float
    social_transfers_share: float
    admin_share: float               # Funds state capacity improvements
    military_share: float            # Contributes to conflict suppression

    # --- Monetary ---
    inflation_target: float          # Central bank target (e.g. 0.02)

    # --- Structural ---
    trade_policy: float              # [−1, 1]: −1 = full protectionism, +1 = full liberalization
```

### 3.3 StepResult

```python
@dataclass
class StepResult:
    state: CountryState              # Updated state after the step
    derived: dict                    # All Tier 2 variables for this year
    reference: dict                  # All Tier 3 metrics for this year
    audit_log: list[AuditEntry]      # Full explainability record
```

---

## 4. Annual Update Sequence

Execute in this exact order. Each step uses **previous-year Tier 1 values** as inputs and writes to new Tier 1 values. No step reads a variable that a later step in the same timestep has already mutated.

```
Step  1.  Validate policy inputs
Step  2.  Update demographics (cohort shares, population)
Step  3.  Update urbanization
Step  4.  Advance human capital pipeline
Step  5.  Compute GDP growth (MRW-delta model)
Step  6.  Apply conflict stability penalty to GDP growth
Step  7.  Update GDP absolute value
Step  8.  Compute output gap
Step  9.  Update inflation (Hybrid NKPC)
Step 10.  Update unemployment (Okun's Law)
Step 11.  Compute fiscal flows (tax revenue, expenditure breakdown)
Step 12.  Update debt dynamics
Step 13.  Update risk premium
Step 14.  Update Gini coefficient
Step 15.  Update life expectancy (Preston Curve delta)
Step 16.  Evaluate conflict risk (logistic)
Step 17.  Update state capacity (Besley-Persson conditional)
Step 18.  Update corruption
Step 19.  Update trade openness
Step 20.  Compute school life expectancy (Tier 2)
Step 21.  Compute reference metrics (Tier 3)
Step 22.  Generate audit log
Step 23.  Apply automatic stabilizers (debt ceiling, unemployment floor)
Step 24.  Increment year, return StepResult
```

---

## 5. Equation Specifications

### 5.1 Validate Policy Inputs

```python
def validate_policy(policy: PolicyInputs) -> list[str]:
    errors = []
    share_sum = (
        policy.health_share + policy.education_share +
        policy.infrastructure_share + policy.social_transfers_share +
        policy.admin_share + policy.military_share
    )
    if abs(share_sum - 1.0) > 0.001:
        errors.append(f"Expenditure shares sum to {share_sum:.3f}, must equal 1.0")
    if not (0.05 <= policy.tax_rate <= 0.55):
        errors.append("Tax rate must be 5%–55% of GDP")
    if not (0.10 <= policy.total_expenditure_gdp <= 0.65):
        errors.append("Total expenditure must be 10%–65% of GDP")
    if errors:
        raise ValueError("\n".join(errors))
```

---

### 5.2 Demographics Update

No cohort-component model in V1. Use closed-form aggregate rules:

```python
# Human capital and life expectancy drive fertility decline over time
delta_youth = (
    -0.0008 * (state.life_expectancy - 65)      # LE above 65 depresses youth share
    - 0.0015 * (state.human_capital - 0.5)       # Education suppresses fertility
)
delta_elderly = (
    +0.0012 * (state.life_expectancy - 65)       # Longer lives expand elderly share
)
delta_working = -(delta_youth + delta_elderly)   # Residual

youth_share_t        = clamp(state.youth_share        + delta_youth,   0.10, 0.52)
elderly_share_t      = clamp(state.elderly_share      + delta_elderly, 0.03, 0.35)
working_age_share_t  = clamp(1.0 - youth_share_t - elderly_share_t,    0.40, 0.80)

# Population growth: implicit from cohort dynamics and historical rate
pop_growth = (
    state.youth_share * 0.045              # Births proxy
    - (1.0 / state.life_expectancy)        # Deaths proxy
)
population_t = state.population * (1 + pop_growth)
```

**Audit causes**: `("le_fertility_effect", delta_youth_le)`, `("education_fertility_effect", delta_youth_hc)`

---

### 5.3 Urbanization

Logistic S-curve with Harris-Todaro wage-gap proxy:

```python
L_max = state.urbanization_capacity      # Country calibration constant
k_base = 0.03                            # Base steepness

# Wage differential proxy: above-trend GDP growth pulls migration
wage_gap = max(0.0, gdp_growth_prev - state.potential_growth)
k = k_base * (1.0 + 10.0 * wage_gap)    # Accelerates during booms

u = state.urban_pop_pct
delta_urban = k * u * (1.0 - u / L_max)
urban_pop_pct_t = clamp(u + delta_urban, u, L_max)  # Never decreases
```

**Audit causes**: `("logistic_base_migration", base_contribution)`, `("wage_differential_pull", wage_contribution)`

---

### 5.4 Human Capital Pipeline

See §8 for full design. Summary equation for step sequencing:

```python
edu_spend_gdp = policy.education_share * policy.total_expenditure_gdp
new_investment = compute_hc_investment(edu_spend_gdp, state.human_capital)

state.hc_pipeline.append(new_investment)
matured = state.hc_pipeline[0]          # Peek — actually popped at end of HC step
# (deque auto-pops left when new entry appended at right via maxlen=15)

hc_depreciation = HC_DEPRECIATION * state.human_capital
human_capital_t = clamp(state.human_capital + matured - hc_depreciation, 0.0, 1.0)
```

---

### 5.5 GDP Growth

Delta model: every contribution is named and separately logged.

```python
# Expenditure breakdown (GDP fractions)
infra_spend_gdp   = policy.infrastructure_share * policy.total_expenditure_gdp
edu_spend_gdp     = policy.education_share      * policy.total_expenditure_gdp

# --- Term 1: Physical capital accumulation ---
# Infrastructure spending above depreciation rate adds to capital stock
capital_accumulation = infra_spend_gdp - DEPRECIATION_RATE
capital_effect = ALPHA * capital_accumulation
# ALPHA = 0.33, DEPRECIATION_RATE = 0.05

# --- Term 2: Human capital (changes are small each year by design) ---
hc_delta = human_capital_t - state.human_capital
hc_effect = (BETA / HC_PIPELINE_LAG) * hc_delta * 50.0
# Scaled because annual delta is tiny; full effect accumulates over pipeline
# BETA = 0.33, HC_PIPELINE_LAG = 15

# --- Term 3: State capacity TFP multiplier ---
# Deviation from 0.5 midpoint shifts TFP linearly
capacity_effect = CAPACITY_GDP_COEFF * (state.legal_capacity - 0.5)
# CAPACITY_GDP_COEFF = 0.03

# --- Term 4: Debt overhang penalty ---
if state.debt_gdp > DEBT_STABILITY_THRESHOLD:           # 0.60
    debt_drag = DEBT_DRAG_COEFF * (state.debt_gdp - DEBT_STABILITY_THRESHOLD)
else:
    debt_drag = 0.0
# DEBT_DRAG_COEFF = 0.02

# --- Term 5: Trade openness bonus (conditional on human capital threshold) ---
if state.human_capital > HC_TRADE_THRESHOLD:            # 0.40
    trade_delta = trade_openness_t - state.trade_openness
    trade_effect = TRADE_GDP_COEFF * trade_delta
else:
    trade_effect = 0.0
# TRADE_GDP_COEFF = 0.10

# --- Composite ---
gdp_growth_raw = (
    state.potential_growth
    + capital_effect
    + hc_effect
    + capacity_effect
    - debt_drag
    + trade_effect
)
```

The conflict stability penalty (Step 6) is applied separately so it appears as a distinct audit cause.

**Audit causes**: `("potential_growth", state.potential_growth)`, `("capital_accumulation", capital_effect)`, `("human_capital_change", hc_effect)`, `("state_capacity_tfp", capacity_effect)`, `("debt_overhang", -debt_drag)`, `("trade_openness", trade_effect)`, `("conflict_penalty", conflict_gdp_adj)`

---

### 5.6 Conflict GDP Penalty

Applied after conflict risk is known from the *previous* timestep (conflict_risk is computed in Step 16 and stored; it applies its GDP penalty in the following year's Step 6).

```python
# Uses conflict_risk computed in previous step
if state.conflict_risk < 0.30:
    conflict_gdp_adj = 0.0
elif state.conflict_risk < 0.50:
    conflict_gdp_adj = -0.005
elif state.conflict_risk < 0.70:
    conflict_gdp_adj = -0.015
else:
    conflict_gdp_adj = -0.030 - 0.020 * (state.conflict_risk - 0.70)

gdp_growth = gdp_growth_raw + conflict_gdp_adj
gdp_t = state.gdp * (1.0 + gdp_growth)
gdp_per_capita_t = gdp_t / population_t
```

---

### 5.7 Output Gap

```python
output_gap = (gdp_growth - state.potential_growth) / max(abs(state.potential_growth), 0.001)
output_gap = clamp(output_gap, -0.30, 0.30)
```

---

### 5.8 Inflation — Hybrid NKPC

```python
# Backward-looking persistence component
backward = INFLATION_PERSISTENCE * state.inflation          # 0.50

# Forward-looking target-anchoring component
forward = (1.0 - INFLATION_PERSISTENCE - 0.20) * policy.inflation_target   # 0.30

# Output gap passthrough
demand_push = NKPC_KAPPA * output_gap                       # κ = 0.08

# Import price passthrough (uses exogenous shock dict; 0 if not provided)
import_shock = external_shocks.get('import_price_change', 0.0)
import_push = PASSTHROUGH_RATE * import_shock * state.trade_openness
# PASSTHROUGH_RATE = 0.30

inflation_t = backward + forward + demand_push + import_push
inflation_t = clamp(inflation_t, -0.05, 2.0)
```

**Audit causes**: `("inflation_persistence", backward)`, `("target_anchor", forward)`, `("demand_push", demand_push)`, `("import_passthrough", import_push)`

---

### 5.9 Unemployment — Okun's Law

```python
delta_u = -OKUN_COEFFICIENT * (gdp_growth - state.potential_growth)
# OKUN_COEFFICIENT = 0.40

unemployment_t = state.unemployment + delta_u

# Floor at structural (NAIRU), ceiling at 40%
unemployment_t = clamp(unemployment_t, state.structural_unemployment, 0.40)
```

**Audit causes**: `("okun_gdp_effect", delta_u)`

---

### 5.10 Fiscal Flows

```python
# Actual revenue is capped by fiscal capacity (tax evasion, collection failure)
tax_revenue_gdp = policy.tax_rate * state.fiscal_capacity

# Expenditure breakdown
health_spend       = policy.health_share            * policy.total_expenditure_gdp
education_spend    = policy.education_share         * policy.total_expenditure_gdp
infra_spend        = policy.infrastructure_share    * policy.total_expenditure_gdp
transfers_spend    = policy.social_transfers_share  * policy.total_expenditure_gdp
admin_spend        = policy.admin_share             * policy.total_expenditure_gdp
military_spend     = policy.military_share          * policy.total_expenditure_gdp

# Primary balance (before interest payments)
primary_balance_gdp = tax_revenue_gdp - policy.total_expenditure_gdp
```

---

### 5.11 Debt Dynamics

Standard intertemporal budget constraint:

```python
nominal_interest = RISK_FREE_RATE + state.risk_premium
# RISK_FREE_RATE = 0.02

nominal_gdp_growth = gdp_growth + inflation_t     # Real growth + inflation deflator

debt_gdp_t = (
    ((1.0 + nominal_interest) / (1.0 + nominal_gdp_growth)) * state.debt_gdp
    - primary_balance_gdp
)
debt_gdp_t = max(debt_gdp_t, 0.0)
```

**Audit causes**: `("interest_burden", interest_contribution)`, `("growth_denominator", growth_contribution)`, `("primary_balance", -primary_balance_gdp)`

---

### 5.12 Risk Premium

Piecewise nonlinear, autoregressive:

```python
def debt_risk_function(debt_gdp: float) -> float:
    if debt_gdp < 0.40:
        return 0.0
    elif debt_gdp < 0.60:
        # Linear: 0 → 0.005 between 40% and 60%
        return 0.005 * (debt_gdp - 0.40) / 0.20
    elif debt_gdp < 0.90:
        # Linear: 0.005 → 0.045 between 60% and 90%
        return 0.005 + 0.040 * (debt_gdp - 0.60) / 0.30
    else:
        # Exponential beyond 90%
        return 0.045 + 0.10 * (debt_gdp - 0.90) ** 2

risk_premium_t = RP_AUTOREGRESSION * state.risk_premium + debt_risk_function(debt_gdp_t)
risk_premium_t = clamp(risk_premium_t, 0.0, 0.25)
# RP_AUTOREGRESSION = 0.85
```

---

### 5.13 Gini Coefficient

Persistent update with named structural drivers:

```python
GINI_PERSISTENCE = 0.90

# Inflation above 5% worsens Gini (regressive wealth erosion)
inflation_push = 0.005 * max(0.0, inflation_t - 0.05)

# Unemployment above structural worsens Gini
unemployment_push = 0.003 * max(0.0, unemployment_t - state.structural_unemployment)

# Human capital above 0.5 reduces Gini (broad education equalizes wages)
hc_pull = -0.008 * (state.human_capital - 0.5)

# Trade openness above 80% can widen skill premium
trade_push = 0.002 * max(0.0, state.trade_openness - 0.80)

# Social transfers directly compress Gini
transfers_pull = -0.010 * max(0.0, transfers_spend - 0.05)

gini_structural = (
    state.gini
    + inflation_push
    + unemployment_push
    + hc_pull
    + trade_push
    + transfers_pull
)

gini_t = GINI_PERSISTENCE * state.gini + (1.0 - GINI_PERSISTENCE) * gini_structural
gini_t = clamp(gini_t, 0.20, 0.70)
```

**Audit causes**: one entry per named driver, only logged if `abs(contribution) > 0.001`

---

### 5.14 Life Expectancy — Preston Curve Delta

```python
import math

# Health spending effect (log — diminishing returns)
health_effect = 0.30 * math.log1p(health_spend * 100)

# Education's independent effect on LE (health behaviors, demand for care)
education_effect = 0.15 * (state.human_capital - 0.5)

# Income effect: log of GDP per capita change
prev_gdppc = state.gdp / state.population
gdppc_delta_log = math.log(gdp_per_capita_t) - math.log(prev_gdppc)
income_effect = clamp(2.0 * gdppc_delta_log, -1.0, 1.0)

# LE ceiling: prevents unrealistic values at given income level
le_ceiling = 60.0 + 18.0 * math.log10(max(gdp_per_capita_t / 1000.0, 0.1) + 1.0)
le_ceiling = clamp(le_ceiling, 45.0, 87.0)

le_target = min(
    state.life_expectancy + health_effect + education_effect,
    le_ceiling
)

# Adjustment speed: 30% of gap per year (prevents jumps)
life_expectancy_t = state.life_expectancy + 0.30 * (le_target - state.life_expectancy) + income_effect * 0.1
life_expectancy_t = clamp(life_expectancy_t, 30.0, 87.0)
```

---

### 5.15 School Life Expectancy (Tier 2)

Computed post-step, informational only:

```python
# SLE is a function of education spend and human capital
base_sle = state.human_capital * 18.0           # Max 18 years at HC = 1.0
spending_boost = 2.0 * (education_spend - 0.04) # Deviation from 4% GDP baseline
school_life_expectancy = clamp(base_sle + spending_boost, 4.0, 20.0)
```

---

## 6. State Capacity Framework

### 6.1 Components

| Variable | Represents | Primary Effect |
|---|---|---|
| `fiscal_capacity` | Fraction of theoretical tax revenue actually collected | Scales `tax_revenue_gdp` directly |
| `legal_capacity` | Institutional quality: property rights, contracts, enforcement | TFP multiplier for GDP; corruption suppression |

Both live on `[0, 1]`. They are **complementary** — one without the other is inefficient. `fiscal_capacity` × `legal_capacity` as a product term may be introduced in V1.5.

### 6.2 Initialization

```python
# Fiscal capacity: from historical Revenue/GDP
# Assumes theoretical max revenue = 40% GDP with perfect capacity
fiscal_capacity_0 = clamp(historical_revenue_gdp / 0.40, 0.05, 0.95)

# Legal capacity: from WGI Rule of Law score (−2.5 to +2.5)
legal_capacity_0 = clamp((rule_of_law_wgi + 2.5) / 5.0, 0.05, 0.95)

# Corruption: inverse of WGI Control of Corruption
corruption_0 = clamp(1.0 - (corruption_wgi + 2.5) / 5.0, 0.02, 0.98)
```

### 6.3 Annual Update — Fiscal Capacity

```python
# --- Investment effect ---
# Admin spending above 1% GDP begins building capacity
admin_invest_effect = 0.020 * (admin_spend / 0.02)   # Normalized: 2% GDP = neutral

# --- Drags ---
corruption_drag      = 0.025 * state.corruption
natural_decay        = CAPACITY_NATURAL_DECAY          # 0.01 — requires maintenance
conflict_degrade     = 0.050 if state.conflict_risk > 0.50 else 0.0

delta_fiscal = admin_invest_effect - corruption_drag - natural_decay - conflict_degrade
fiscal_capacity_t = clamp(state.fiscal_capacity + delta_fiscal, 0.05, 0.95)
```

### 6.4 Annual Update — Legal Capacity

Legal capacity responds more slowly to investment and degrades more severely under conflict:

```python
legal_invest_effect  = 0.015 * (admin_spend / 0.02)   # Builds slightly slower
corruption_drag_l    = 0.030 * state.corruption        # More corruption-sensitive
conflict_degrade_l   = 0.080 if state.conflict_risk > 0.50 else 0.0

delta_legal = legal_invest_effect - corruption_drag_l - natural_decay - conflict_degrade_l
legal_capacity_t = clamp(state.legal_capacity + delta_legal, 0.05, 0.95)
```

### 6.5 Corruption Update

```python
# Legal capacity suppresses corruption
corruption_reduction = 0.020 * state.legal_capacity

# Conflict and poverty push corruption up
conflict_push  = 0.030 * max(0.0, state.conflict_risk - 0.40)
poverty_push   = 0.010 * max(0.0, 0.5 - gdp_per_capita_t / 20000.0)

delta_corruption = conflict_push + poverty_push - corruption_reduction
corruption_t = clamp(state.corruption + delta_corruption, 0.02, 0.98)
```

---

## 7. Human Capital Framework

### 7.1 Design

Human capital is a stock that reflects the educational attainment of the active workforce. The pipeline system enforces the 15-year lag mechanically — not via a decay parameter or a coefficient — so the temporal structure is transparent and explainable to both developer and player.

**Player-visible implication**: If you cut education spending today, the damage does not appear in human capital for 15 years. If you restore spending, recovery also lags 15 years. The pipeline queue makes this auditable.

### 7.2 Investment Function — Diminishing Returns

```python
def compute_hc_investment(edu_spend_gdp: float, current_hc: float) -> float:
    """
    Convert this year's education spend into a pipeline addition.
    The pipeline addition materializes as human_capital gain in 15 years.
    
    At 5% GDP spend (global average): raw_invest ≈ 0.002
    At HC = 0 (bottom): full effect
    At HC = 0.8 (near-ceiling): 60% reduction in returns
    """
    # Normalize: 5% of GDP is the baseline reference
    spend_ratio = edu_spend_gdp / 0.05
    raw_invest = spend_ratio * 0.002

    # Diminishing returns: already-educated populations gain less per dollar
    dr_factor = 1.0 - 0.60 * current_hc
    
    return raw_invest * dr_factor
```

### 7.3 Pipeline Initialization

```python
from collections import deque

def initialize_hc_pipeline(
    state: CountryState,
    historical_edu_spend: list[float]   # Last 15 years, oldest to newest
) -> deque:
    """
    Backfill pipeline with 15 years of historical education investments.
    If fewer than 15 years are available, pad the start with the earliest known value.
    """
    if len(historical_edu_spend) >= 15:
        spend_series = historical_edu_spend[-15:]
    else:
        padding_value = historical_edu_spend[0] if historical_edu_spend else 0.04
        spend_series = [padding_value] * (15 - len(historical_edu_spend)) + historical_edu_spend

    return deque(
        [compute_hc_investment(s, state.human_capital) for s in spend_series],
        maxlen=15
    )
```

### 7.4 Annual Step

```python
def step_human_capital(
    state: CountryState,
    edu_spend_gdp: float
) -> tuple[float, float, float]:
    """
    Returns: (human_capital_t, matured_investment, hc_depreciation)
    """
    new_investment = compute_hc_investment(edu_spend_gdp, state.human_capital)

    # append() on a maxlen deque automatically pops the oldest (leftmost) entry
    state.hc_pipeline.append(new_investment)
    matured = state.hc_pipeline[0]          # The popleft() happened implicitly via maxlen
    # Note: after append on full deque, index [0] is now what was [1] before. 
    # Capture matured BEFORE appending, or use appendleft trick.
    # Correct implementation:
    #   matured = state.hc_pipeline[0]         # oldest, about to be pushed out
    #   state.hc_pipeline.append(new_investment)  # pushes out oldest

    hc_depreciation = HC_DEPRECIATION * state.human_capital   # HC_DEPRECIATION = 0.003

    human_capital_t = clamp(state.human_capital + matured - hc_depreciation, 0.0, 1.0)

    return human_capital_t, matured, hc_depreciation
```

**Audit causes**: `("pipeline_matured_investment", matured)`, `("workforce_depreciation", -hc_depreciation)`

---

## 8. Political Stability Framework

### 8.1 Conflict Risk — Logistic Function

```python
import math

def compute_conflict_risk(state: CountryState, unemployment_t: float,
                          gdp_growth: float, gini_t: float,
                          inflation_t: float, military_spend: float) -> float:

    # --- Normalized inputs ---
    # Youth bulge: centered so that 15% youth share = 0 (neutral)
    youth_norm        = (state.youth_share - 0.15) / 0.20

    # Unemployment above structural rate (only excess matters)
    unemp_excess      = max(0.0, unemployment_t - state.structural_unemployment - 0.03)

    # Urban-youth interaction: high urban density amplifies youth bulge tension
    urban_youth       = state.urban_pop_pct * max(0.0, youth_norm)

    # Inequality only destabilizing above Gini 0.40
    gini_excess       = max(0.0, gini_t - 0.40)

    # Only negative GDP growth contributes
    recession_drag    = max(0.0, -gdp_growth)

    # Inflation only destabilizing above 10%
    inflation_stress  = max(0.0, inflation_t - 0.10)

    # --- Logistic predictor ---
    eta = (
        state.conflict_intercept                         # Country baseline (CALIB)
        + CONFLICT_YOUTH_COEFF       * youth_norm        # 0.80
        + CONFLICT_UNEMP_COEFF       * unemp_excess      # 0.50
        + CONFLICT_URBAN_COEFF       * urban_youth       # 0.60
        + CONFLICT_GINI_COEFF        * gini_excess       # 0.70
        + CONFLICT_RECESSION_COEFF   * recession_drag    # 0.60
        + CONFLICT_INFLATION_COEFF   * inflation_stress  # 0.40
        - CONFLICT_CAPACITY_PROTECT  * state.legal_capacity  # 0.50
        - CONFLICT_MILITARY_SUPPRESS * military_spend    # 0.30
    )

    return 1.0 / (1.0 + math.exp(-eta))
```

### 8.2 Conflict Intercept Calibration

`conflict_intercept` is fitted per country at initialization so that the logistic function reproduces the historical `political_stability` WGI score at baseline:

```python
def calibrate_conflict_intercept(state: CountryState, historical_stability_wgi: float) -> float:
    """
    Solve for conflict_intercept such that compute_conflict_risk()
    returns a conflict_risk consistent with the historical WGI score.
    
    WGI Political Stability maps to conflict_risk as:
        conflict_risk = 1.0 - (political_stability_wgi + 2.5) / 5.0
    """
    target_risk = clamp(1.0 - (historical_stability_wgi + 2.5) / 5.0, 0.01, 0.99)
    target_logit = math.log(target_risk / (1.0 - target_risk))

    # Compute the sum of all covariate terms with intercept = 0
    eta_without_intercept = compute_conflict_eta_no_intercept(state)

    # Intercept = target logit - covariate sum
    return target_logit - eta_without_intercept
```

### 8.3 Stability Bands and Downstream Effects

| Band | Conflict Risk | GDP Adj (next year) | Capacity Investment | Audit Label |
|---|---|---|---|---|
| Stable | < 0.30 | 0.0% | Full | `STABLE` |
| Stressed | 0.30–0.50 | −0.5% | Half | `STRESSED` |
| Unstable | 0.50–0.70 | −1.5% | Blocked | `UNSTABLE` |
| Crisis | > 0.70 | −3.0% to −5.0% | Blocked + degradation | `CRISIS` |

In Crisis band, state capacity degrades actively regardless of admin investment (see §6.3).

### 8.4 Political Stability Score (WGI-compatible)

```python
# Maps [0, 1] conflict_risk back to [−2.5, +2.5] WGI scale for display
political_stability_score = 2.5 - (5.0 * conflict_risk)
```

---

## 9. Policy System

### 9.1 Policy Lever → Variable Transmission

| Lever | Immediate Effect | Lagged Effect | Mechanism |
|---|---|---|---|
| `tax_rate ↑` | `tax_revenue ↑`, possible `gdp_growth ↓` (crowding) | — | Fiscal capacity caps collection; drag on private sector if rate too high |
| `education_share ↑` | Nothing immediate | `human_capital ↑` in 15 years | Pipeline system §8 |
| `health_share ↑` | `life_expectancy` begins moving toward new target | Full LE effect in 5–10 years | Preston Curve delta §5.14 |
| `infrastructure_share ↑` | `gdp_growth ↑` next year | Sustained for 3–5 years | Capital accumulation term §5.5 |
| `social_transfers_share ↑` | `gini ↓` | — | Transfers pull in Gini equation §5.13 |
| `admin_share ↑` | `fiscal_capacity` and `legal_capacity` begin rising | Full effect in 3–5 years | Besley-Persson step §6 |
| `military_share ↑` | `conflict_risk ↓` | — | Suppression term in logistic §8.1 |
| `inflation_target ↓` | Slight `inflation ↓` next year | Converges over 3–5 years | Forward-looking NKPC weight |
| `trade_policy +1` | `trade_openness` moves toward 1.5× current | GDP effect if HC threshold met | §5.19, §5.5 trade term |
| `total_expenditure ↑` | `primary_balance ↓`, `debt_gdp ↑` | Risk premium reprices in 1–3 years | Debt dynamics §5.11 |

### 9.2 Trade Openness Update

```python
# Trade openness converges toward a target set by policy
trade_policy_target = state.trade_openness * (1.0 + 0.30 * policy.trade_policy)
# +1.0 policy = aims for 30% higher openness; −1.0 = 30% lower

# Converges at ~20% per year (structural adjustment lag)
trade_openness_t = state.trade_openness + 0.20 * (trade_policy_target - state.trade_openness)
trade_openness_t = clamp(trade_openness_t, 0.0, 2.0)
```

### 9.3 Automatic Stabilizers

Applied in Step 23, these override player policy under extreme conditions:

```python
# --- 1. Sovereign pressure constraint ---
# If debt > 90%, bond markets force primary surplus adjustment
if debt_gdp_t > DEBT_CRITICAL_THRESHOLD:        # 0.90
    forced_consolidation = 0.005 * (debt_gdp_t - DEBT_CRITICAL_THRESHOLD) * 10
    effective_expenditure_gdp = policy.total_expenditure_gdp - forced_consolidation
    # Log as AuditEntry with cause "sovereign_pressure_constraint"
else:
    effective_expenditure_gdp = policy.total_expenditure_gdp

# --- 2. Unemployment safety net floor ---
# Minimum social transfer regardless of player allocation
if unemployment_t > 0.20:
    min_transfer_gdp = 0.01
    if transfers_spend < min_transfer_gdp:
        # Reallocate from largest non-essential bucket
        # Log as AuditEntry with cause "unemployment_safety_net"
        pass
```

---

## 10. Calibration & Normalization

### 10.1 Country Initialization Protocol

```python
def initialize_country(
    country_code: str,
    start_year: int,
    db_conn,
    historical_window: int = 5
) -> CountryState:

    # Load from SQLite data warehouse
    baseline = load_year(db_conn, country_code, start_year)
    history  = load_range(db_conn, country_code,
                          start_year - historical_window, start_year - 1)

    state = CountryState(country_code=country_code, year=start_year)

    # --- Direct mappings ---
    state.gdp              = baseline['gdp']
    state.inflation        = baseline['inflation']
    state.unemployment     = baseline['unemployment']
    state.debt_gdp         = baseline['debt_gdp']
    state.population       = baseline['population']
    state.youth_share      = baseline['youth_share']      / 100.0
    state.working_age_share= baseline['working_age_share']/ 100.0
    state.elderly_share    = baseline['elderly_share']    / 100.0
    state.urban_pop_pct    = baseline['urban_population_pct'] / 100.0
    state.life_expectancy  = baseline['life_expectancy']
    state.gini             = baseline['gini']
    state.trade_openness   = baseline['trade_openness']

    # --- Normalized governance variables ---
    state.legal_capacity   = normalize_wgi(baseline['rule_of_law'])
    state.fiscal_capacity  = clamp(baseline['revenue_gdp'] / 0.40, 0.05, 0.95)
    state.corruption       = clamp(1.0 - normalize_wgi(baseline['corruption_index']), 0.02, 0.98)

    # --- Human capital ---
    state.human_capital    = compute_education_index(baseline)
    state.hc_pipeline      = initialize_hc_pipeline(
                                 state,
                                 [h.get('education_spend_gdp', 0.04) for h in history]
                             )

    # --- Risk premium: bootstrapped from debt level ---
    state.risk_premium     = debt_risk_function(state.debt_gdp)

    # --- Calibration constants ---
    growth_series          = [h['gdp_growth'] for h in history if 'gdp_growth' in h]
    state.potential_growth = trimmed_mean(growth_series, trim=0.10) if growth_series else 0.025

    unemp_series           = [h['unemployment'] for h in history if 'unemployment' in h]
    state.structural_unemployment = min(unemp_series) if unemp_series else 0.05

    state.urbanization_capacity = min(0.95, state.urban_pop_pct + 0.20)

    # --- Conflict intercept: fitted to historical political stability ---
    state.conflict_intercept = calibrate_conflict_intercept(
                                   state, baseline['political_stability']
                               )

    return state
```

### 10.2 Helper Functions

```python
def normalize_wgi(wgi_score: float) -> float:
    """WGI [−2.5, +2.5] → [0, 1]"""
    return clamp((wgi_score + 2.5) / 5.0, 0.0, 1.0)

def compute_education_index(baseline: dict) -> float:
    """Reproduce UNDP Education Index from MYS and EYS where available"""
    mys = baseline.get('mean_years_schooling', 8.0)
    eys = baseline.get('expected_years_schooling', 12.0)
    return ((min(mys, 15.0) / 15.0) + (min(eys, 18.0) / 18.0)) / 2.0

def trimmed_mean(values: list[float], trim: float = 0.10) -> float:
    n = len(values)
    k = max(1, int(n * trim))
    return sum(sorted(values)[k:-k]) / max(len(sorted(values)[k:-k]), 1)

def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
```

---

## 11. Explainability System

### 11.1 AuditEntry

```python
@dataclass
class AuditEntry:
    year: int
    variable: str                             # e.g. "gdp_growth"
    value: float                              # New value after step
    delta: float                              # Change from previous timestep
    causes: list[tuple[str, float]]           # [(cause_label, contribution_magnitude)]
    severity: str                             # "none" | "notable" | "significant" | "critical"
    note: str = ""                            # Optional plain-English summary
```

### 11.2 Severity Thresholds

```python
SEVERITY_THRESHOLDS: dict[str, tuple[float, float, float]] = {
    # variable: (notable_delta, significant_delta, critical_delta)
    "gdp_growth":       (0.010, 0.030, 0.060),
    "inflation":        (0.020, 0.050, 0.150),
    "unemployment":     (0.010, 0.025, 0.050),
    "debt_gdp":         (0.030, 0.080, 0.150),
    "conflict_risk":    (0.050, 0.120, 0.250),
    "fiscal_capacity":  (0.020, 0.050, 0.100),
    "legal_capacity":   (0.020, 0.050, 0.100),
    "human_capital":    (0.005, 0.015, 0.030),
    "life_expectancy":  (0.500, 1.500, 3.000),
    "gini":             (0.005, 0.020, 0.050),
}

def classify_severity(variable: str, abs_delta: float) -> str:
    thresholds = SEVERITY_THRESHOLDS.get(variable, (0.01, 0.05, 0.10))
    if abs_delta < thresholds[0]:  return "none"
    if abs_delta < thresholds[1]:  return "notable"
    if abs_delta < thresholds[2]:  return "significant"
    return "critical"
```

### 11.3 Usage Pattern

Every equation block appends to an `audit_entries` list before returning. Entries with `severity == "none"` are collected but suppressed in the UI by default. The front-end queries `[e for e in audit_log if e.severity != "none"]` for the player-facing report, and the full log for developer debugging.

```python
# Example: after computing GDP growth
audit_entries.append(AuditEntry(
    year=state.year,
    variable="gdp_growth",
    value=gdp_growth,
    delta=gdp_growth - prev_gdp_growth,
    causes=[
        ("potential_growth",      state.potential_growth),
        ("capital_accumulation",  capital_effect),
        ("human_capital_change",  hc_effect),
        ("state_capacity_tfp",    capacity_effect),
        ("debt_overhang",        -debt_drag),
        ("trade_openness",        trade_effect),
        ("conflict_penalty",      conflict_gdp_adj),
    ],
    severity=classify_severity("gdp_growth", abs(gdp_growth - prev_gdp_growth)),
    note=f"GDP grew {gdp_growth:.1%} vs potential {state.potential_growth:.1%}"
))
```

---

## 12. Key Constants

Group all magic numbers in a single `constants.py`. Every constant references the mechanism it encodes.

```python
# constants.py

# --- Production Function (MRW) ---
ALPHA                       = 0.33     # Physical capital output elasticity
BETA                        = 0.33     # Human capital output elasticity
DEPRECIATION_RATE           = 0.05     # Annual physical capital depreciation

# --- GDP Growth Effects ---
CAPACITY_GDP_COEFF          = 0.03     # Legal capacity → TFP shift per 0.1 unit
DEBT_STABILITY_THRESHOLD    = 0.60     # Debt/GDP above which overhang penalty applies
DEBT_CRITICAL_THRESHOLD     = 0.90     # Debt/GDP above which sovereign pressure fires
DEBT_DRAG_COEFF             = 0.02     # GDP drag per unit debt above stability threshold
HC_TRADE_THRESHOLD          = 0.40     # Minimum human capital for trade gains to accrue
TRADE_GDP_COEFF             = 0.10     # Trade openness delta → GDP growth contribution

# --- Inflation (Hybrid NKPC) ---
INFLATION_PERSISTENCE       = 0.50     # γ_b: backward-looking weight
NKPC_KAPPA                  = 0.08     # κ: output gap passthrough coefficient
PASSTHROUGH_RATE            = 0.30     # Import price passthrough fraction

# --- Unemployment ---
OKUN_COEFFICIENT            = 0.40     # β: Okun's Law coefficient

# --- Debt & Sovereign Risk ---
RISK_FREE_RATE              = 0.02     # Exogenous global risk-free rate
RP_AUTOREGRESSION           = 0.85     # ρ: risk premium autoregressive persistence

# --- Gini ---
GINI_PERSISTENCE            = 0.90     # Structural persistence of inequality

# --- Human Capital Pipeline ---
HC_PIPELINE_LAG             = 15       # Years from education investment to workforce entry
HC_DEPRECIATION             = 0.003    # Annual human capital depreciation (cohort retirement)

# --- State Capacity ---
CAPACITY_NATURAL_DECAY          = 0.010    # Annual decay without maintenance investment
CAPACITY_CORRUPTION_DRAG_F      = 0.025    # Corruption → fiscal capacity drag
CAPACITY_CORRUPTION_DRAG_L      = 0.030    # Corruption → legal capacity drag (higher)
CAPACITY_CONFLICT_DEGRADE_F     = 0.050    # Conflict > 0.5 → fiscal capacity degradation
CAPACITY_CONFLICT_DEGRADE_L     = 0.080    # Conflict > 0.5 → legal capacity degradation

# --- Political Stability (Logistic) ---
CONFLICT_YOUTH_COEFF            = 0.80     # Youth bulge coefficient
CONFLICT_UNEMP_COEFF            = 0.50     # Unemployment excess coefficient
CONFLICT_URBAN_COEFF            = 0.60     # Urban-youth interaction coefficient
CONFLICT_GINI_COEFF             = 0.70     # Gini excess coefficient
CONFLICT_RECESSION_COEFF        = 0.60     # Negative GDP growth coefficient
CONFLICT_INFLATION_COEFF        = 0.40     # Inflation stress coefficient
CONFLICT_CAPACITY_PROTECT       = 0.50     # Legal capacity protection coefficient
CONFLICT_MILITARY_SUPPRESS      = 0.30     # Military spend suppression coefficient

# --- Urbanization ---
URBANIZATION_K                  = 0.03     # Base logistic steepness
```

---

## 13. V1 / V1.5 / V2 Roadmap

### V1 — Foundation

**Goal**: A working, testable simulation engine. All 14 variables update correctly. Player can run a 30-year simulation and read an annual audit log.

**Deliverables**:
- `CountryState` and `PolicyInputs` dataclasses
- `constants.py` with all parameters
- `SimulationEngine.step()` implementing all 24 update steps in order
- Country initialization from existing SQLite warehouse
- `AuditEntry` generation for every material variable change
- CLI or test runner: load a country, simulate 20 years with flat policy, print annual summary table

**Success criteria**: A country initialized at its 2015 historical baseline, given policy inputs equal to its 2010–2015 historical averages, must produce 2025 outputs within ±20% of actual 2025 values for GDP per capita, inflation, unemployment, debt/GDP, and life expectancy.

**Explicitly out of scope for V1**: random shocks, events, multi-country, regime type, financial sector, age arrays.

---

### V1.5 — Simulation Quality

**Goal**: Replayable, calibrated, player-facing. Adds variance, events, and per-country tuning.

New features:
1. **Exogenous shock layer**: Gaussian noise on GDP growth (`σ = 0.01`), inflation (`σ = 0.005`), import prices. Seeded RNG for reproducibility.
2. **Event system**: Rule-based triggers fire narrative events with optional player choices (e.g., `debt_gdp > 0.90` → "IMF Consultation" event with austerity or default branches).
3. **Per-country parameter calibration**: Replace global coefficient defaults with country-fitted values for `potential_growth`, `structural_unemployment`, `OKUN_COEFFICIENT`, and `NKPC_KAPPA` using the historical dataset.
4. **Dynamic potential growth**: `potential_growth` updates slowly based on prolonged human capital and capacity changes (5-year rolling average of actual growth, weighted).
5. **Policy look-ahead**: A `simulate_preview(state, policy, n_years=5)` function that runs a deterministic 5-year projection without shocks, for player advisory display.
6. **School Life Expectancy** properly computed and surfaced as a Tier 2 variable with audit entry.

---

### V2 — Full Simulation

**Goal**: Deep simulation capable of complex multi-decade campaign play across diverse country archetypes.

New modules:
1. **Cohort-component demographics**: 20-band age array (0–4, 5–9, ..., 95+) with survival probabilities scaled by life expectancy. Enables proper demographic dividend and aging crisis modelling.
2. **Education pipeline by cohort**: Track which age cohort is currently in school vs. workforce. Education investment affects specific entering cohorts.
3. **Regime type system**: Democracy, hybrid, and autocracy each constrain available policy ranges and modify the conflict risk and state capacity equations.
4. **Multi-country trade**: Countries have bilateral trade relationships. Trade openness depends on partner policies and bilateral agreements, not just domestic settings.
5. **Natural resource module**: Resource rents feed fiscal capacity but suppress diversification (Dutch Disease on manufacturing TFP); resource curse dynamics on institutional quality.
6. **Civil conflict state**: When `conflict_risk > 0.80`, transition to an explicit conflict state with modelled duration, intensity, war economy effects, and resolution conditions.
7. **Financial sector**: Basic credit cycle — private investment separated from public infrastructure spend, with credit boom/bust dynamics affecting GDP and unemployment.
8. **Environmental productivity drag**: Slow-moving TFP drag from environmental degradation index; natural disaster shocks.
