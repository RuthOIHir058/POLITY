# POLITY Engine

POLITY is a deterministic, explainable country-level political-economy simulation engine. Version 1.0.0 implements the authoritative V1 guidebook as a closed-form annual model with explicit policy transmission, governance filtration, macro-fiscal dynamics, social outcomes, and a causal audit log for every simulated year.

> Release status: the V1 implementation is complete and tested. Historical calibration does not yet meet the guidebook's stated acceptance target; the evidence is reported openly in [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md). No software license has yet been selected. See [LICENSE_PENDING.md](LICENSE_PENDING.md) before reusing or redistributing the code.

![POLITY five-layer architecture](docs/assets/polity_five_layer_architecture.png)

## Scientific motivation

POLITY is designed for researchers who need a model that is easier to inspect than an agent-based simulation or an optimized DSGE system, while retaining explicit economic and institutional mechanisms. The design is built around four constraints:

- Explainability: every material variable change has named causes and magnitudes.
- Determinism: identical initial state, policy, and external shocks produce identical output.
- Calibration discipline: country initialization is grounded in a historical SQLite warehouse and model limitations are measured rather than hidden.
- Tractability: all V1 equations are closed-form arithmetic with no machine learning, agent population, or optimization loop.

The engine is a research simulation, not a forecast, causal estimator, or policy recommendation system.

## Architecture

The model follows five layers:

1. Global context supplies deterministic external shock values. V1 defaults every shock to zero.
2. Policy intent validates fiscal, expenditure, monetary, and trade choices and applies automatic stabilizers.
3. State filtration translates policy through corruption, legal capacity, fiscal capacity, and conflict conditions.
4. The economic core updates GDP, inflation, unemployment, fiscal flows, debt, sovereign risk, and trade openness.
5. Societal outcomes update demographics, urbanization, human capital, inequality, health, conflict risk, and display-only reference metrics.

`SimulationEngine.step()` executes the 24 guidebook phases in order. It reads from a deep prior-year snapshot, computes local candidate values, and returns a new `CountryState`, derived metrics, reference metrics, and a complete `AuditEntry` list. See [ARCHITECTURE.md](ARCHITECTURE.md) for the module map and update sequence.

## Features

- Canonical decimal-unit `CountryState` and validated `PolicyInputs` contracts.
- Exact 15-year human-capital investment queue.
- MRW-delta growth decomposition with separately logged capital, human-capital, capacity, debt, trade, and conflict terms.
- Hybrid NKPC inflation, Okun unemployment, intertemporal debt dynamics, and nonlinear sovereign risk.
- Calibrated conflict-risk logistic, stability bands, state-capacity investment, and corruption dynamics.
- Demographic shares, population growth, logistic urbanization, Gini, Preston-curve life expectancy, school-life expectancy, and HDI reference metrics.
- Automatic sovereign-pressure and unemployment safety-net constraints.
- Country initialization from a bundled, integrity-checked SQLite snapshot.
- CLI, CSV output, JSON policy files, executable examples, data rebuild tooling, and CI.
- Full causal audit records, including entries normally suppressed by a player-facing interface because their severity is `none`.

## Implementation status

| Area | V1 status |
|---|---|
| 24-step annual orchestration | Implemented |
| Guidebook equation modules | Implemented |
| Country initialization and normalization | Implemented |
| Explainability and severity classification | Implemented |
| Determinism and input immutability | Verified |
| CLI and CSV export | Implemented |
| Automated tests | 60 passing |
| Branch coverage | 93% |
| 20-year country execution | 122 countries initialized and simulated |
| Historical calibration target | Not met by the documented proxy |
| Random shocks and event system | Deferred to V1.5 |
| Multi-country trade and cohort arrays | Deferred to V2 |

The detailed pre-implementation audit is in [docs/implementation/SPEC_AUDIT.md](docs/implementation/SPEC_AUDIT.md), and the completed work is summarized in [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md).

## Requirements

- Python 3.11, 3.12, or 3.13.
- SQLite support in the Python standard library.
- No third-party packages are required to run the core engine.
- `pytest` and `coverage` are pinned for development and verification.
- `requests`, `pandas`, and `openpyxl` are optional and used only by data acquisition or ETL workflows.

See [INSTALL.md](INSTALL.md) for operating-system-specific setup.

## Installation

```bash
git clone https://github.com/RuthOlHir058/POLITY.git
cd POLITY
python -m venv .venv
```

Activate the environment, then install the development profile:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

The editable install exposes the `polity` command. A core-only install is available with:

```bash
python -m pip install -r requirements.txt
```

## Quick start

Run a three-year Kenya simulation with the publication policy:

```bash
polity KEN --start-year 2015 --years 3 \
  --policy-file configs/baseline_policy.json
```

Representative V1.0.0 output:

```text
POLITY V1 | KEN | start 2015 | 3 deterministic years
year  growth   gdp_pc    inflation  unemployment  debt_gdp  life_exp  conflict
2016   -0.24%      1481      1.49%         4.21%     53.1%     62.42     74.5%
2017   -0.58%      1468     -1.05%         5.80%     65.3%     62.56     75.8%
2018   -1.05%      1449     -2.33%         7.58%     83.1%     62.70     77.3%
```

Write a 20-year annual summary to CSV:

```bash
polity KEN --start-year 2015 --years 20 \
  --policy-file configs/baseline_policy.json \
  --output results/kenya_baseline.csv
```

Print all notable, significant, and critical audit entries:

```bash
polity KEN --start-year 2015 --years 5 --audit
```

The legacy-compatible entry point is also supported:

```bash
python main.py KEN --start-year 2015 --years 5
```

A complete beginner workflow is in [QUICKSTART.md](QUICKSTART.md).

## Python API example

```python
from engine.cli import DEFAULT_POLICY
from engine.core.initialize_country import initialize_country
from engine.core.simulation_engine import SimulationEngine

initial = initialize_country("KEN", 2015)
results = SimulationEngine.simulate(initial, DEFAULT_POLICY, years=20)

final = results[-1]
print(final.state.year)
print(final.derived["gdp_per_capita"])
print(final.reference["hdi"])

for entry in final.audit_log:
    if entry.severity != "none":
        print(entry.variable, entry.delta, entry.causes)
```

`simulate()` does not mutate `initial`. Reusing the same initial state for policy comparisons is therefore safe and deterministic.

## Policy inputs

A policy file is one JSON object containing all fields below. Fiscal values are fractions of GDP; expenditure shares must sum to 1.0.

```json
{
  "tax_rate": 0.40,
  "total_expenditure_gdp": 0.24,
  "health_share": 0.15,
  "education_share": 0.20,
  "infrastructure_share": 0.20,
  "social_transfers_share": 0.20,
  "admin_share": 0.15,
  "military_share": 0.10,
  "inflation_target": 0.02,
  "trade_policy": 0.00
}
```

The CLI also accepts individual overrides such as `--tax-rate 0.35` or `--trade-policy 0.20`; command-line values take precedence over a policy file.

## Expected outputs

Each annual `StepResult` contains:

- `state`: persistent Tier-1 variables for the new year.
- `derived`: fresh Tier-2 values such as GDP growth, GDP per capita, output gap, tax revenue, primary balance, conflict risk, political stability, and school-life expectancy.
- `reference`: display-only Tier-3 values such as HDI and schooling years. These values never feed back into the model.
- `audit_log`: named causes, contribution magnitudes, deltas, severity, and a plain-language note.

CSV output includes the principal macro, social, conflict, and reference metrics. It does not flatten the full audit log; use the Python API for complete causal records.

## Repository structure

```text
POLITY/
|-- engine/                     # Scientific package and public CLI
|   |-- core/                   # Contracts, constants, initialization, orchestration
|   |-- policy/                 # Validation and automatic stabilizers
|   |-- governance/             # Fiscal/legal capacity and corruption
|   |-- politics/               # Conflict-risk and stability framework
|   |-- economy/                # Growth, inflation, unemployment, fiscal and debt
|   |-- society/                # Demographics, HC, inequality, health, references
|   |-- trade/                  # Trade-openness convergence
|   |-- global_context/         # Deterministic external-shock contract
|   `-- data/                   # Warehouse adapter and packaged database copy
|-- tests/                      # Unit, integration, and smoke tests
|-- docs/                       # Specification, audit, data, verification, assets
|-- examples/                   # Beginner and comparative simulation scripts
|-- data/                       # Published SQLite snapshot and data staging notes
|-- configs/                    # Reproducible JSON policy configurations
|-- tools/                      # Download, ETL, and validation modules
|-- scripts/                    # Security and release verification entry points
|-- README.md                  # Project overview and primary usage guide
|-- INSTALL.md                 # Windows, Linux, and macOS installation
|-- QUICKSTART.md              # First simulation and policy editing
|-- ARCHITECTURE.md            # Five-layer model and deterministic data flow
|-- IMPLEMENTATION_REPORT.md   # Guidebook implementation decisions
|-- VERIFICATION_REPORT.md     # Tests, coverage, validation, calibration
|-- SECURITY_AUDIT.md          # Publication security review and exclusions
|-- CHANGELOG.md               # Versioned release history
|-- CONTRIBUTING.md            # Development and scientific-change process
|-- RELEASE_NOTES_v1.0.0.md    # GitHub release notes
|-- PUBLISHING.md              # Safe owner-authenticated GitHub commands
|-- pyproject.toml             # Package metadata and pinned optional profiles
|-- requirements*.txt          # Reproducible install profiles
`-- LICENSE_PENDING.md         # Explicit notice: no license selected
```

## Testing and release verification

Run the complete suite and enforce branch coverage:

```bash
python -m coverage erase
python -m coverage run --branch -m pytest
python -m coverage report --fail-under=90
```

Run publication-level checks:

```bash
python -m compileall -q engine tools examples scripts main.py
python -m tools.validation.check_schema
python -m tools.validation.check_loader_contract
python -m tools.validation.check_database_sync
python -m tools.validation.check_determinism --years 20
python scripts/verify_release.py
python scripts/security_scan.py --root .
```

The historical calibration proxy is deliberately separate because it reports an unmet scientific criterion rather than a software test failure:

```bash
python -m tools.validation.historical_calibration_proxy
```

See [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md) for exact results and interpretation.

## Reproducibility notes

- The core model uses no random number generator in V1.
- External shocks default to an all-zero immutable value object.
- All policy and state ratios use decimal fractions inside the engine; warehouse percentages are converted once during initialization.
- The two published database copies are byte-identical and checked in CI.
- The publication database SHA-256 is recorded in [docs/data/DATA_PROVENANCE.md](docs/data/DATA_PROVENANCE.md).
- Exact numeric replay assumes the same POLITY release, input database, Python implementation, country, start year, policy, number of years, and external-shock sequence.
- The bundled warehouse contains both historical observations and, for some fiscal series, provider projections. Review the source year before treating a value as observed history.

## Limitations

- The guidebook's 2015-to-2025 five-indicator acceptance test cannot be executed as written because the bundled warehouse has no country with all five required 2025 observations.
- A documented 2015-to-2024 proxy found zero of 113 comparable countries passing all five +/-20% thresholds. This is a model-calibration failure, not a test-suite failure.
- The warehouse lacks historical category-level expenditure shares and historical military expenditure. The proxy therefore uses a fixed disclosed expenditure split.
- Current-USD GDP is used to initialize a real-growth model. Exchange-rate and GDP-deflator effects are not separately represented.
- Missing baseline fields prevent 174 of 296 country records from initializing at 2015; 122 complete a 20-year run.
- V1 has no stochastic shocks, event system, regime types, financial sector, natural-resource module, bilateral trade, or detailed age cohorts.
- Output is scenario-dependent model behavior and should not be presented as a forecast or causal policy estimate.

## Roadmap

V1.5 is intended to add seeded exogenous shocks, events, country-specific parameter fitting, dynamic potential growth, policy previews, and improved calibration tooling. V2 is intended to add cohort demographics, education by cohort, regime constraints, bilateral trade, natural resources, explicit conflict states, a financial sector, and environmental productivity effects. Roadmap items are not commitments until implemented and tested.

## Citation

Until a DOI or archival citation is issued, cite the tagged software release and the authoritative specification:

```text
POLITY contributors. POLITY Engine, version 1.0.0. GitHub repository,
https://github.com/RuthOlHir058/POLITY, 2026.
```

For research use, also identify the exact tag, database checksum, country, start year, policy file, and external-shock configuration. The repository includes [CITATION.cff](CITATION.cff) for citation-manager support.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Scientific changes must preserve equation traceability and include numerical regression tests. Security concerns should follow [SECURITY.md](SECURITY.md), not a public issue when disclosure could expose users.

## License

No license has been selected. [LICENSE_PENDING.md](LICENSE_PENDING.md) is not a license grant. Source publication alone does not authorize reuse, modification, or redistribution beyond rights provided by applicable law. Third-party data remains subject to its providers' terms.
