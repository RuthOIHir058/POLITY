# POLITY V1 Complete Implementation Plan

> Historical document: this was the implementation plan used for V1. Completion and verification status are reported in the top-level `IMPLEMENTATION_REPORT.md` and `VERIFICATION_REPORT.md`.

## Phase 1 — Canonical contracts and invariants

1. Replace `CountryState` with the authoritative Tier-1 state in decimal units.
2. Add the required persisted `conflict_risk` and internal `previous_gdp_growth` reconciliation fields.
3. Centralize all guidebook constants, ranges, severity thresholds, and mechanism labels.
4. Correct the Tier 1/2/3 variable registry.
5. Add shared `clamp`, safe-log, and dataclass-copy helpers.

**Exit test:** state construction and range validation; no raw warehouse/reference fields in Tier 1.

## Phase 2 — Layer 2 policy interface

1. Implement complete validation of expenditure shares, fiscal bounds, individual share bounds, inflation target, and trade policy.
2. Implement deterministic expenditure breakdown.
3. Implement sovereign-pressure consolidation and unemployment safety-net reallocation as an effective-policy result with explicit causes.

**Exit test:** valid policy passes; each invalid dimension raises a descriptive `ValueError`; stabilizer tie-breaking is deterministic.

## Phase 3 — Layer 3 governance and political filtration

1. Implement conflict logistic predictor, stable/stressed/unstable/crisis bands, WGI mapping, and intercept calibration.
2. Implement fiscal/legal capacity updates with full/half/blocked investment conditional on prior conflict risk.
3. Implement corruption update.

**Exit test:** calibration reproduces target baseline risk; capacity bands and conflict degradation match thresholds.

## Phase 4 — Layer 4 economic engine

1. Implement trade target and convergence as pure functions.
2. Implement MRW-delta growth decomposition and piecewise conflict penalty.
3. Implement output gap, hybrid NKPC, Okun's Law, fiscal flows, debt dynamics, and nonlinear autoregressive risk premium.
4. Expose every contribution separately for audit construction.

**Exit test:** unit tests reproduce guidebook worked formulas exactly to floating-point tolerance.

## Phase 5 — Layer 5 society and reference outcomes

1. Implement aggregate demographics and population growth.
2. Implement logistic urbanization using previous growth.
3. Implement HC investment, historical queue initialization, and correct capture-before-append annual step.
4. Implement Gini, Preston-curve life expectancy, school life expectancy, and Tier-3 HDI/schooling metrics.

**Exit test:** cohort shares sum to one within tolerance; HC policy changes mature only after the specified queue delay; reference metrics are not read by model functions.

## Phase 6 — 24-step orchestration and explainability

1. Build `SimulationEngine.step()` around a deep prior-state snapshot and local candidate values.
2. Preserve the guidebook order and avoid same-year state mutation.
3. Add optional deterministic external shock input with a zero default; no random generation.
4. Assemble complete derived/reference dictionaries.
5. Generate audit entries for all state changes and derived outputs, classify severity, and include stabilizer entries.
6. Commit a new state and increment the year.
7. Make `SimulationStep` a compatibility facade.

**Exit test:** input immutability, deterministic equality, exact audit coverage, one-year range invariants, and multi-year repeatability.

## Phase 7 — Initialization and warehouse adapter

1. Add connection/path-safe `load_year`, `load_range`, and metadata functions.
2. Resolve required baseline values through nearest historical observations; preserve source rows as dictionaries.
3. Implement direct mappings and percentage-to-ratio conversion.
4. Implement governance normalization, education index, HC queue backfill, debt risk bootstrap, trimmed historical potential growth, structural unemployment, urban capacity, and conflict intercept calibration.
5. Keep a compatibility `load_country()` convenience function returning initialized canonical state.

**Exit test:** Kenya 2015 and 2023 initialize with all required fields in declared ranges; loader contract validation passes from any working directory.

## Phase 8 — CLI, tests, documentation, cleanup

1. Replace `main.py` with a country/year/year-count CLI and annual summary table.
2. Replace print-only smoke scripts with pytest assertions and add unit/integration tests for every equation family.
3. Add a flat-policy 20-year integration test and a baseline replay diagnostic against available historical data.
4. Update README and architecture documentation.
5. Remove stale engine backup files, caches, and unrelated scratch code from the deliverable.

**Exit test:** full pytest suite, compile check, CLI simulation, data validators, and deterministic output checksum pass.

## Final verification artifacts

- `docs/implementation/SPEC_AUDIT.md`
- `docs/implementation/IMPLEMENTATION_PLAN.md`
- `docs/implementation/VERIFICATION_REPORT.md`
- updated source tree
- packaged `polity_v1_implemented.tar.gz`
