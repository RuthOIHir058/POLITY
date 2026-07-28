# POLITY V1 Implementation Report

## Purpose

This report summarizes the completed conversion of the POLITY handoff from an early warehouse-shaped prototype into the deterministic V1 engine defined by the authoritative guidebook. It explains what changed, why the architecture changed, how guidebook requirements map to modules, and where explicit reconciliations were necessary.

No scientific coefficient or equation was changed during publication preparation. Release work was limited to repository cleanup, packaging, documentation, verification, data-tool hardening, and public interfaces.

## Starting point

The handoff contained a useful SQLite warehouse and several core dataclasses, but the annual engine was not a partial implementation of the specified model. The original design mixed raw data fields, percentages, persisted state, derived values, and display metrics in one object. Most required annual mechanisms were absent or used different equations.

The full pre-implementation comparison is preserved in [docs/implementation/SPEC_AUDIT.md](docs/implementation/SPEC_AUDIT.md). The implementation sequence is preserved in [docs/implementation/IMPLEMENTATION_PLAN.md](docs/implementation/IMPLEMENTATION_PLAN.md).

Principal original gaps included:

- warehouse percentages used directly where the equations require decimal ratios;
- in-place state mutation;
- no complete 24-phase annual sequence;
- placeholder simulation-step code;
- incomplete or empty policy, economy, governance, politics, society, trade, and global-context packages;
- incorrect GDP, conflict, output-gap, inflation, unemployment, debt, risk-premium, and initialization behavior;
- no demographics, urbanization, 15-year human-capital maturation, Gini, life expectancy, trade convergence, reference metrics, or automatic stabilizers;
- audit entries without a causal decomposition;
- print-only smoke scripts rather than assertion-based tests;
- stale engine snapshots and local development artifacts inside the source tree.

## Completed architecture

### Canonical contracts

The implementation defines the public contracts in `engine/core`:

- `CountryState`: canonical persistent state in decimal units.
- `PolicyInputs`: immutable annual policy values.
- `AuditEntry`: value, delta, ordered causes, severity, and note.
- `StepResult`: state, Tier-2 derived values, Tier-3 references, and full audit log.
- `constants.py`: one authoritative coefficient and threshold registry.
- `variable_registry.py`: explicit Tier-1, Tier-2, and Tier-3 names.

Raw source fields do not enter annual model functions. Initialization is the only percentage-to-ratio conversion boundary.

### Layered equation modules

The previously empty domain packages now contain pure, testable equation functions:

| Layer | Modules | Implemented mechanisms |
|---|---|---|
| Global context | `global_context/shocks.py` | Explicit deterministic external-shock contract and zero defaults |
| Policy | `policy/validation.py`, `policy/stabilizers.py` | Input bounds, expenditure breakdown, sovereign pressure, transfer floor |
| Governance and politics | `governance/capacity.py`, `politics/stability.py` | Conflict logistic, intercept calibration, stability bands, capacity, corruption |
| Economy | `economy/macro.py`, `economy/fiscal.py`, `trade/openness.py` | MRW-delta growth, NKPC, Okun, fiscal flows, debt, risk, trade convergence |
| Society | `society/*.py` | Demographics, urbanization, HC queue, Gini, life expectancy, SLE, HDI references |

Each domain function returns a structured calculation containing both the new value and named contributions. This lets the engine build causal audit entries from the equation output rather than from undocumented reconstruction logic.

### Annual orchestration

`SimulationEngine.step()` now represents all 24 guidebook phases. It clones the prior state, computes local values, assembles a new state only after all equations have read the prior snapshot, and returns a complete `StepResult`.

`SimulationEngine.simulate()` repeatedly calls `step()` without mutating the supplied initial state. `SimulationStep` remains only as a compatibility facade and delegates to the authoritative engine.

### Initialization and data boundary

`engine/data/country_loader.py` now supports:

- explicit database paths or existing SQLite connections;
- country metadata lookup;
- one-year and inclusive range loading;
- allowlisted nearest-value lookup;
- consistent errors for missing countries or databases.

`engine/core/initialize_country.py` now performs:

- one-time unit conversion;
- governance normalization;
- education-index construction;
- human-capital queue backfill;
- risk-premium bootstrap;
- historical potential-growth estimation;
- structural-unemployment calibration;
- urbanization-capacity initialization;
- conflict-intercept calibration;
- explicit failure when required historical fields do not exist.

### Explainability

Every changed Tier-1 variable and each exposed Tier-2 or Tier-3 value receives an audit entry. Causes retain the labels and contribution magnitudes of their source equation. Severity thresholds are centralized and variable-specific.

The audit system answers both numerical and narrative questions:

- What is the new value?
- How much did it change?
- Which mechanisms contributed?
- What was each mechanism's magnitude?
- Is the change notable, significant, or critical under the registered threshold?

### Public interfaces

The release adds:

- the `polity` console command;
- JSON policy loading with unknown-key and numeric-type rejection;
- command-line policy overrides;
- stable annual CSV output;
- optional material audit output;
- executable beginner and policy-comparison examples;
- a backward-compatible `python main.py` entry point.

## Guidebook compliance by mechanism

| Requirement | Implementation |
|---|---|
| Policy validation and share sum | `engine/policy/validation.py` |
| Demographic aggregate update | `engine/society/demographics.py` |
| Logistic urbanization | `engine/society/urbanization.py` |
| 15-year HC queue | `engine/society/human_capital.py` |
| MRW-delta GDP growth | `engine/economy/macro.py` |
| Piecewise conflict GDP penalty | `engine/economy/macro.py` |
| Output gap | `engine/economy/macro.py` |
| Hybrid NKPC | `engine/economy/macro.py` |
| Okun unemployment | `engine/economy/macro.py` |
| Fiscal-capacity revenue | `engine/economy/fiscal.py` |
| Debt dynamics | `engine/economy/fiscal.py` |
| Nonlinear risk premium | `engine/economy/fiscal.py` |
| Gini drivers | `engine/society/inequality.py` |
| Preston-curve life expectancy | `engine/society/health.py` |
| School-life expectancy | `engine/society/health.py` |
| Conflict logistic and WGI mapping | `engine/politics/stability.py` |
| Fiscal/legal capacity | `engine/governance/capacity.py` |
| Corruption update | `engine/governance/capacity.py` |
| Trade convergence | `engine/trade/openness.py` |
| Tier-3 references | `engine/society/reference_metrics.py` |
| Audit causes and severity | `engine/core/simulation_engine.py`, `constants.py` |
| Automatic stabilizers | `engine/policy/stabilizers.py` |
| Country initialization | `engine/core/initialize_country.py` |

## Major architectural decisions

### 1. Raw data and simulation state are separate

Reason: the handoff stored percentages and provider columns directly in the state. That allowed the same value to be interpreted in incompatible units and made Tier boundaries impossible to enforce.

Decision: loaders return raw dictionaries. Initialization constructs the canonical state and converts units exactly once. Domain functions accept only canonical values.

### 2. Annual execution is snapshot-based

Reason: in-place mutation would let later equations observe an arbitrary mixture of current- and previous-year values, contrary to the update contract.

Decision: `step()` deep-clones the input, reads from that prior snapshot, stores equation outputs locally, and assembles the new state at the end.

### 3. Equation functions return causes

Reason: an audit log generated only after state changes cannot reliably reconstruct the mechanism decomposition.

Decision: each domain calculation returns its value and cause terms. The orchestrator converts those terms into typed audit entries.

### 4. Constants are centralized

Reason: duplicated numbers caused coefficient drift in the prototype, including incorrect trade and recession coefficients.

Decision: all model coefficients, limits, severity thresholds, and defaults live in `engine/core/constants.py` with mechanism-oriented names.

### 5. Automatic stabilizers use one fixed recomputation

Reason: the guidebook evaluates stabilizers at Step 23, after debt and transfers have already been computed. Merely changing a local policy object at that point cannot affect the returned state.

Decision: compute an ordinary candidate, derive an effective constrained policy, and recompute once from the original prior snapshot. A fixed single recomputation prevents recursive feedback and preserves determinism.

### 6. Publication database copies are verified byte-for-byte

Reason: a source checkout naturally reads `data/database/polity.db`, while a packaged installation needs data inside the package.

Decision: include a second copy at `engine/data/polity.db` and enforce SHA-256 equality in CI. The copies are not independent datasets.

## Specification reconciliations

The guidebook contains dependencies or conflicts that require an implementation choice. The following choices preserve the numerical equations and are visible in code and tests.

### Persisted conflict risk

The declared `CountryState` listing omits `conflict_risk`, but the GDP penalty and capacity equations require the previous year's risk. The implementation persists it as internal Tier-1 timing state. Current risk is computed at Step 16 and influences GDP and capacity in the following annual step.

### Previous GDP growth

Urbanization requires `gdp_growth_prev`, but GDP growth is otherwise Tier 2 and not persisted. The implementation retains `previous_gdp_growth` solely for this dependency. It initializes to potential growth.

### Prospective trade value

The GDP equation at Step 5 requires `trade_openness_t`, while the update order commits trade at Step 19. The implementation calculates the pure Step-19 candidate before growth, uses only its delta in the growth term, and commits it at Step 19.

### Stabilizer effect

The explicit single recomputation described above is required for the Step-23 policy override to affect the returned year. Stabilizer decisions and causes are included in the audit record.

### Capacity conflict threshold

The detailed fiscal and legal capacity equations specify degradation whenever prior conflict risk is above 0.50. A summary table describes degradation only for the crisis band. The implementation follows the explicit equations, which are more specific and directly parameterized.

### Life-expectancy bounds

The Tier-1 registry permits values through 88, while the annual Preston equation explicitly clamps to 87. Initialization accepts the registry range; annual updates follow the explicit 87-year equation clamp.

### Historical military baseline

The warehouse has no historical military-expenditure series. Conflict-intercept calibration therefore uses a zero baseline military contribution. This is not fitted or silently inferred.

### Corruption source scale

The warehouse contains a Transparency International CPI-style 0-to-100 value rather than a WGI Control of Corruption value. Initialization detects that scale and maps it to `1 - CPI/100`. WGI-form inputs continue to use the guidebook normalization.

### Human-capital pipeline history

The warehouse lacks historical education expenditure. The implementation uses the guidebook's explicit 4 percent of GDP fallback for unavailable queue years.

## Data and tooling changes for publication

The release retains the verified aggregate SQLite snapshot and excludes raw third-party files. Download and ETL modules were made path-safe and import-safe:

- network scripts use explicit timeouts, a descriptive user agent, and atomic writes;
- no acquisition script requires a key, token, cookie, or stored credential;
- raw and database destinations can be supplied through command-line arguments or documented non-secret environment variables;
- ETL updates use allowlisted columns and upserts rather than obsolete destructive schema scripts;
- modules use `main()` guards and can be imported by tests without running work;
- the UNDP loader updates its actual source year instead of overwriting every year;
- obsolete schema versions, seed scripts, scratch code, caches, and engine backups were removed.

These changes do not alter annual scientific equations.

## Test implementation

The release replaces print-only checks with unit, integration, and smoke tests. Coverage includes:

- contract validation and cloning;
- helper functions and bounded behavior;
- demographic, urbanization, health, inequality, and HC timing;
- GDP, inflation, unemployment, fiscal, debt, risk, trade, capacity, and conflict equations;
- policy validation and stabilizer paths;
- initialization and warehouse access;
- exact determinism and input immutability;
- audit completeness;
- CLI policy merging, errors, audit output, and CSV output;
- executable examples;
- 20-year CLI and model runs.

The final suite contains 60 tests and reports 93 percent branch-aware coverage. Full evidence is in [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md).

## Known scientific limitation

The guidebook defines successful V1 calibration as reproducing five 2025 outcomes within +/-20 percent under historical-average policy. The warehouse cannot support that exact test because no country has all five 2025 observations. The closest documented proxy uses 2024, available 2010-to-2015 fiscal averages, and a fixed disclosed expenditure split.

Zero of 113 comparable countries passed all five proxy targets. Mongolia passed four; Kenya passed only life expectancy. The implementation was not tuned by replacing equations or hiding this outcome. Calibration remains the principal scientific blocker after the software implementation.

## Publication preparation

The publication tree was created from a clean copy rather than turning the development worktree into a release in place. Preparation included:

- exhaustive source, hidden-file, archive, database, OOXML, PNG-metadata, and binary-string security scanning;
- exclusion of a raw workbook containing a local workstation path in document metadata;
- removal of caches, backup snapshots, scratch code, runtime outputs, raw downloads, and obsolete schema scripts;
- stripped image metadata;
- pinned development and data-tool dependencies;
- continuous-integration checks for Python 3.11, 3.12, and 3.13;
- installation, quick-start, architecture, security, data-provenance, contribution, release, and verification documentation;
- logical Conventional Commit history and the `v1.0.0` tag.

No credentials were added, and no GitHub token is required or accepted by the repository.

## Outcome

The V1 codebase now matches the guidebook's specified architecture and equations, is deterministic under identical inputs, provides complete causal audit records, supports reproducible installation and execution, and is structured for independent research review.

The software implementation is complete. Scientific calibration is not complete, and that distinction is maintained throughout the release documentation.
