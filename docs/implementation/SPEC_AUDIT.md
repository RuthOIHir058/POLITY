# POLITY V1 Specification Audit

> Historical document: this audit records the pre-implementation handoff. The listed gaps have been addressed unless retained as an explicit limitation in the top-level implementation and verification reports.

Authoritative source: `polity_engine_v1_spec.md` supplied with the handoff.

Audit date: 2026-07-28

## Executive finding

The handoff contains a usable historical SQLite warehouse and several early engine contracts, but the simulation itself is a prototype that does not implement the V1 specification. The dominant defect is a boundary failure: raw warehouse fields and units are embedded directly in the persistent simulation state. That causes percentage/fraction errors, Tier-2 and Tier-3 persistence, missing state, incorrect calibration, and equations that cannot be composed safely.

## Specification reconciliations required before implementation

The guidebook contains four internal dependencies that are not fully represented in its declared structures. They are resolved as follows, without changing any numeric equation:

1. `conflict_risk` is persisted in `CountryState`. Sections 5.6, 6.3-6.5, and 8 require the previous year's risk, even though it is omitted from the Section 3.1 dataclass.
2. `previous_gdp_growth` is retained as internal engine state. Section 5.3 requires `gdp_growth_prev`, while Tier 2 values otherwise are not available to a later `step(state, policy)` call. It is initialized to `potential_growth` and stores only the prior annual growth needed by urbanization.
3. The Step-19 trade value is computed prospectively as a pure local value for the Step-5 trade delta, then committed at Step 19. This resolves the explicit use of `trade_openness_t` in Section 5.5 without mutating a later-step state variable early.
4. Automatic stabilizers are applied through one fixed recomputation when triggered. Step 23 first evaluates the ordinary candidate state, creates an effective policy, and recomputes the same closed-form annual path once. Without this reconciliation, the supplied Step-23 pseudocode has no causal effect on debt, transfers, or any downstream variable.

## Core discrepancy matrix

| Module | Current implementation | Specification gap | Required action |
|---|---|---|---|
| `engine/core/country_state.py` | Warehouse-shaped dataclass; raw and simulated values mixed; ratios mostly stored as percentages; Tier 2/3 fields persisted | Does not match the Tier-1 registry; wrong names and units; missing canonical `gdp`, `urban_pop_pct`; carries raw source columns and reference metrics | Replace with canonical simulation state, calibration constants, `conflict_risk`, and narrowly scoped internal prior-growth state |
| `engine/core/policy_inputs.py` | Correct field names and plausible defaults | No range validation for shares, inflation target, trade policy, or individual shares | Keep contract; add policy validation in Layer 2 and convenience expenditure method |
| `engine/core/audit_entry.py` | Shape mostly matches | Allows `None` values/deltas; no validation; engine supplies no causes | Tighten typed contract and generate complete named-cause records |
| `engine/core/step_result.py` | Shape matches | Existing engine leaves reference outputs empty and derived registry incomplete | Retain and populate all Tier 2/Tier 3 outputs |
| `engine/core/constants.py` | Partial registry | `TRADE_GDP_COEFF=0.02` instead of `0.10`; recession coefficient `0.40` instead of `0.60`; obsolete risk heuristic constants; several mechanism constants absent | Replace with one authoritative constants registry |
| `engine/core/variable_registry.py` | Incorrect Tier assignments and names | Persists GDP per capita, current account, potential growth, political stability; omits demographics and several required derived variables | Replace with exact V1 Tier registry plus documented internal fields |
| `engine/core/initialize_country.py` | Mutates an already-loaded warehouse-shaped state | Fiscal capacity uses government effectiveness rather than revenue; corruption direction/source wrong; HDI incorrectly enters human capital; pipeline stores HC levels rather than investments; risk and potential growth equations wrong; no structural unemployment, urban cap, or conflict calibration | Rebuild around `initialize_country(country_code, start_year, db_conn, historical_window)` and guidebook formulas |
| `engine/core/simulation_engine.py` | In-place prototype implementing fragments of macro/fiscal logic | Missing 18+ annual steps; wrong units; wrong GDP equation; multiplicative conflict penalty; wrong output gap, NKPC, Okun, debt, risk; no demographics, HC, Gini, LE, conflict, capacity, corruption, trade, references, stabilizers; empty audit causes | Replace with immutable-snapshot orchestrator for all 24 steps |
| `engine/core/simulation_step.py` | Explicit placeholder | Duplicate public runner returns no simulated change | Convert to compatibility facade delegating to `SimulationEngine.step()` |
| `engine/data/country_loader.py` | Opens a relative DB path and directly constructs simulation state | No raw/canonical separation, no history loader, no missing-data policy, no connection injection, unsafe row indexing | Add `load_year`, `load_range`, country metadata lookup, path/connection support, and clear errors |
| `main.py` | Prints a title only | V1 requires a 20-year flat-policy CLI/test runner | Implement deterministic CLI with annual summary and optional audit output |

## Equation defects in the current engine

| Mechanism | Current behavior | Required behavior |
|---|---|---|
| Demographics | Not implemented | Closed-form youth/elderly/working shares and population equation |
| Urbanization | Not implemented | Logistic S-curve with previous-growth wage-gap acceleration |
| Human capital | Not implemented in annual step | 15-year investment queue with correct capture-before-append behavior and depreciation |
| Physical capital contribution | Not implemented | `ALPHA * (infrastructure_spend_gdp - 0.05)` |
| Human-capital GDP effect | Not implemented | `(BETA / 15) * hc_delta * 50` |
| Capacity GDP effect | Average fiscal/legal level | Legal-capacity deviation from 0.5 only |
| Debt overhang | Penalizes all debt | Applies only above 0.60 |
| Trade GDP effect | Level effect, wrong coefficient | Delta effect, HC threshold, coefficient 0.10 |
| Conflict GDP effect | Multiplicative `growth * (1-risk)` | Four piecewise stability bands using previous risk |
| Output gap | Raw growth difference | Potential-normalized and clamped to [-0.30, 0.30] |
| Inflation | Persistence plus gap only; percent conversion | Hybrid NKPC with target anchor and optional import passthrough, all in ratios |
| Unemployment | Uses raw output gap, no NAIRU | Okun change from growth minus potential; structural floor and 0.40 ceiling |
| Tax revenue | Equal to policy tax rate | Policy target multiplied by fiscal capacity |
| Debt | Prior debt minus balance | Standard interest/growth budget constraint |
| Risk premium | Linear debt/deficit heuristic | Piecewise nonlinear debt function plus 0.85 autoregression |
| Gini | Not implemented | Persistent named structural drivers |
| Life expectancy | Not implemented | Preston-curve delta with spending, education, income, and ceiling |
| Conflict risk | Not implemented | Calibrated logistic function and WGI-compatible score |
| State capacity | Not implemented | Conditional admin investment, corruption/decay/conflict drags, stability bands |
| Corruption | Not implemented | Legal suppression plus conflict and poverty pushes |
| Trade openness | Not implemented | 20% convergence to policy target |
| School life expectancy | Persisted raw warehouse field | Tier-2 post-step function only |
| HDI/reference | Persisted historical values | Tier-3 post-step values never read back |
| Stabilizers | Not implemented | Sovereign consolidation and unemployment transfer floor with audit causes |

## Missing modules / five-layer architecture violations

The packages `engine/policy`, `engine/economy`, `engine/governance`, `engine/politics`, `engine/society`, `engine/trade`, and `engine/global_context` contain only empty `__init__.py` files. The project diagram and specification require these concerns to be separate from the orchestration layer. The implementation will add pure modules for policy validation/stabilization, macro/fiscal equations, governance capacity, political stability, demographics/human capital/social outcomes, trade adjustment, and deterministic external shocks.

The `engine/events`, `engine/climate`, and `engine/ai_nations` packages are intentionally empty and remain out of scope because the guidebook assigns those mechanisms to V1.5 or V2.

## Supporting module inventory

Every implemented Python module in the archive was inspected. Modules not containing V1 model equations are classified below.

### Data acquisition modules

The following are one-shot download scripts and do not participate in `step()`: `download_cpi.py`, `download_elderly_share.py`, `download_exports_gdp.py`, `download_gdp.py`, `download_gdp_per_capita.py`, `download_gini.py`, `download_imf_fiscal.py`, `download_imports_gdp.py`, `download_inflation.py`, `download_life_expectancy.py`, `download_median_age.py`, `download_population.py`, `download_population_growth.py`, `download_school_life_expectancy.py`, `download_undp_hdi.py`, `download_unemployment.py`, `download_urban_population.py`, `download_wgi.py`, `download_world_bank.py`, and `download_youth_share.py`. They are outside the V1 simulation specification and will be retained. No random or model behavior is imported from them.

### ETL modules

The following populate the existing warehouse and are outside annual equation execution: `create_schema.py`, `create_schema_v2.py`, `create_schema_v3.py`, `init_database.py`, `load_cpi.py`, `load_demographics.py`, `load_gdp.py`, `load_gdp_per_capita.py`, `load_gini.py`, `load_imf_current_account.py`, `load_imf_fiscal.py`, `load_inflation.py`, `load_life_expectancy.py`, `load_population.py`, `load_population_growth.py`, `load_school_life_expectancy.py`, `load_trade_openness.py`, `load_undp_hdi.py`, `load_unemployment.py`, `load_urban_population.py`, `load_wgi.py`, `load_world_bank_countries.py`, and `seed_kenya.py`. They remain unchanged unless a validation import must be updated. The database itself is treated as historical input, not simulation state.

### Validation modules

`check_schema.py`, `check_missing_data.py`, `check_country_coverage.py`, and `check_year_ranges.py` validate the warehouse and remain applicable. `check_loader_contract.py` targets the obsolete warehouse-shaped `CountryState` and must be rewritten for the canonical state and unit invariants.

### Existing tests

All seven `tests/smoke` files are print-only scripts with no assertions. They encode the obsolete percentage-based state contract. They will be replaced with automated tests that fail on equation, unit, sequencing, determinism, or audit regressions.

### Non-production artifacts

`simulation_engine.py.bak`, `simulation_engine.py.pre_macro`, `simulation_engine.py.pre_inflation`, and `simulation_engine.py.pre_fiscal` are stale source snapshots inside the import tree. They are not executable modules but create ambiguity and will be removed after the new engine passes tests. `scratch_ilo_test.py` is unrelated exploratory code and will be moved out of the production root or removed.

## Data-source mismatches requiring deterministic normalization

- Warehouse fiscal, debt, inflation, unemployment, demographic-share, Gini, and trade values are percentages; the simulation uses decimal ratios. Conversion occurs exactly once at initialization.
- The warehouse `corruption_index` is CPI-style 0-100 rather than WGI Control of Corruption. Initialization uses `1 - CPI/100` when the value lies on the 0-100 scale, and uses the guidebook WGI normalization when the input lies on the -2.5 to +2.5 scale.
- Historical education expenditure is absent. The guidebook's own fallback of 4% GDP is used for every unavailable pipeline year.
- Some baseline rows contain nulls. Initialization uses the nearest same-country historical observation for required fields, with documented guidebook defaults only when no observation exists.

## Acceptance criteria

Implementation is complete only when:

- all 24 annual steps are represented in order;
- all Tier-1 variables are updated only by named equations;
- every changed Tier-1 variable and every Tier-2 output has an audit entry with named causes;
- identical state, policy, and shocks yield structurally equal results;
- the input state is unchanged after `step()`;
- the HC lag is exactly 15 queue advances;
- state shares and all bounded variables remain within their declared ranges;
- the CLI runs at least 20 deterministic years;
- all warehouse validations and the new automated test suite pass.
