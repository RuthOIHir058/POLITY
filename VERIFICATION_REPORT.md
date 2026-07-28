# POLITY V1 Verification Report

Release: `v1.0.0`  
Verification date: 2026-07-28  
Local verification runtime: CPython 3.13.5 on Linux

## Verification scope

This report covers:

- automated tests;
- branch-aware engine coverage;
- source compilation;
- database integrity and schema contracts;
- loader and state-range validation;
- deterministic equality and input immutability;
- multi-record 20-year simulation execution;
- installable wheel and source-distribution behavior;
- historical calibration evidence and limitations.

Security verification is documented separately in [SECURITY_AUDIT.md](SECURITY_AUDIT.md).

## Summary

| Check | Result |
|---|---|
| Automated tests | 60 passed |
| Engine branch-aware coverage | 93% |
| Coverage floor | Passed at 90% |
| Source compilation | Passed |
| SQLite schema validation | Passed |
| Database-copy SHA-256 sync | Passed |
| Loader contract and state ranges | Passed |
| Exact repeated 20-year simulation | Passed |
| Input state unchanged | Passed |
| 2015 initialization and 20-year run | 122 records succeeded; 174 lacked required fields |
| Wheel build and installed CLI smoke test | Passed |
| Source distribution, rebuild, tests, and installed CLI smoke test | Passed |
| Exact guidebook 2025 calibration test | Not executable from available observations |
| Disclosed 2015-2024 proxy | 0 of 113 records passed all five targets |

## Automated test suite

Command:

```bash
python -m pytest
```

Result:

```text
60 passed
```

The suite contains unit, integration, and subprocess smoke tests. It covers:

- state, policy, audit, and result contracts;
- range and finite-value validation;
- demographic and population equations;
- urbanization and the prior-growth wage-gap channel;
- human-capital investment, queue maturation, depreciation, and the exact lag;
- GDP-growth decomposition and conflict penalty bands;
- output gap, inflation, unemployment, fiscal flow, debt, and sovereign risk;
- Gini, life expectancy, schooling, and reference metrics;
- conflict risk, intercept calibration, state capacity, and corruption;
- policy validation and both automatic stabilizers;
- the full 24-phase annual engine;
- input immutability and repeated deterministic equality;
- country initialization and unit conversion;
- SQLite connection and loader error paths;
- CLI policy files, overrides, audit output, CSV output, and failure handling;
- example scripts and 20-year process execution;
- the `SimulationStep` compatibility facade.

## Coverage

Commands:

```bash
python -m coverage erase
python -m coverage run --branch -m pytest
python -m coverage report --fail-under=90
```

Result:

```text
TOTAL: 1325 statements, 53 missed, 228 branches, 41 partial, 93% coverage
```

Coverage is configured for the installable `engine` package and includes branch measurement. The publication floor is 90%.

Lower-covered areas are primarily defensive initialization branches for rare missing-data combinations and exceptional stabilizer-reallocation paths. Core constants, contracts, helpers, reference metrics, CLI, simulation facade, and most equation modules are at or near full coverage.

Coverage is not used as a substitute for equation review. The detailed specification audit remains part of the release.

## Source compilation

Command:

```bash
python -m compileall -q engine tools examples scripts main.py
```

Result: passed with no syntax or import-compilation error.

## Database validation

### Schema and rows

Command:

```bash
python -m tools.validation.check_schema
```

Result:

| Table | Rows |
|---|---:|
| `countries` | 296 |
| `economic_indicators` | 20,318 |
| `governance_indicators` | 5,489 |
| `societal_indicators` | 16,969 |

All expected columns and primary keys matched `docs/data/schema_reference.sql`.

### Year ranges

Command:

```bash
python -m tools.validation.check_year_ranges
```

Result:

- economic indicators: 1800-2031;
- governance indicators: 1996-2024;
- societal indicators: 1960-2025.

The economic table includes source projections. These ranges do not imply complete observations for every field and code.

### Snapshot identity

Command:

```bash
python -m tools.validation.check_database_sync
```

Result:

```text
6dfd602f35a2cec9309c09d5073059e6a7b9041c6e5ff2cea17e25476b4a79d6
```

The researcher-facing and package-facing SQLite files are byte-identical.

### Loader contract

Command:

```bash
python -m tools.validation.check_loader_contract --country KEN --year 2023
```

The loader produced all 26 `CountryState` fields, populated required values, converted ratios correctly, and passed `CountryState.validate_ranges()`.

## Determinism and input immutability

Command:

```bash
python -m tools.validation.check_determinism --country KEN --year 2015 --years 20
```

The test:

1. initializes Kenya at 2015;
2. clones the input state;
3. runs the same policy for 20 years twice;
4. canonicalizes state, derived values, reference values, and every audit entry as sorted JSON;
5. requires byte-for-byte equality;
6. requires the original input state to remain equal to its clone.

Result: passed.

Canonical SHA-256 fingerprint:

```text
991843772a64d354addc4496c5e493c295a946fbf0e9cf45cd912ed6a5008d22
```

This fingerprint is tied to the tagged source, database snapshot, policy, Python numeric behavior, and canonical serialization used by the verifier.

## Multi-record execution validation

Command:

```bash
python scripts/verify_release.py
```

The verifier iterated over every record in the `countries` table, attempted a 2015 initialization, and ran every successful initialization for 20 years under the same valid policy.

Results:

- total code records: 296;
- initialized and simulated for 20 years: 122;
- not initializable because at least one required historical field was absent: 174;
- runtime failures after successful initialization: 0.

This is an execution and invariant check, not evidence that all 122 paths are empirically calibrated. Some master records are regional aggregates or non-sovereign entries rather than countries.

The verifier also checked the Kenya deterministic path and reported 29 audit entries in the final modeled year.

## Packaging verification

### Runtime wheel

Wheel build command:

```bash
python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
```

The pure-Python wheel built successfully with 43 files. It contains the scientific `engine` package, the compatibility `main` module, console-entry-point metadata, and the packaged SQLite database. The packaged database retained SHA-256 `6dfd602f35a2cec9309c09d5073059e6a7b9041c6e5ff2cea17e25476b4a79d6`.

Repository-only tests, tools, scripts, documentation, raw-data directories, build products, and caches are absent from the wheel. Because no license has been selected, the wheel contains no `License` or `License-File` metadata and does not misclassify `LICENSE_PENDING.md` as a license grant.

The wheel was installed into a fresh virtual environment without downloading dependencies. From a working directory outside the repository, the installed package successfully ran:

```bash
polity --version
polity KEN --start-year 2023 --years 1 --output installed-smoke.csv
python -m main --version
```

The installed CLI and CSV export therefore do not depend on the repository-relative database path.

### Source distribution

The source distribution contains 166 files, including complete source, tests, documentation, examples, configs, validation and security tools, verification artifacts, both checked database copies, and `LICENSE_PENDING.md`. Raw provider workbooks, caches, backups, and local outputs are absent.

The extracted source distribution passed all 60 tests, source compilation, database-copy verification, and the exact 20-year determinism check. A wheel was then rebuilt from that extracted source, installed in a separate fresh virtual environment, and used to run the installed CLI and CSV export successfully.

The wheel extraction passed the publication security scanner with zero findings. Standard generated `*.egg-info` metadata inside the source distribution was scanned separately as six text files with zero secret or personal-information findings; after removing that packaging-only metadata, the remaining 160 extracted files passed the full scanner with zero findings.

## Continuous integration configuration

`.github/workflows/ci.yml` is configured to run on Python 3.11, 3.12, and 3.13. It performs a clean-tree security scan before dependency installation, installs pinned development dependencies, enforces branch coverage, compiles source, validates the database and loader, checks determinism, runs the release-wide execution check and disclosed historical proxy on Python 3.13, removes generated artifacts, and scans the tree and reachable Git history again.

The workflow was prepared locally but was not executed on GitHub during this publication task because no authenticated GitHub session was available. Local success must not be represented as a completed remote CI run.

## Historical calibration assessment

### Guidebook success criterion

The guidebook requires a record initialized in 2015 and given its 2010-2015 historical policy averages to reproduce actual 2025 values within +/-20% for:

- GDP per capita;
- inflation;
- unemployment;
- debt/GDP;
- life expectancy.

The bundled warehouse contains **zero** 2025 records with all five required observations. The exact criterion cannot be executed from this release data.

Historical category-level expenditure shares are also absent, so a complete historical `PolicyInputs` reconstruction is unavailable.

### Disclosed 2015-2024 proxy

Command:

```bash
python -m tools.validation.historical_calibration_proxy
```

The proxy is explicitly not the guidebook's 2025 acceptance test. It uses 2024 because 158 warehouse records have all five 2024 target observations before intersecting with initialization eligibility.

For each initializable record, the proxy constructs policy inputs as follows:

- `tax_rate`: mean 2010-2015 observed revenue/GDP divided by baseline fiscal capacity, then clamped to the allowed policy range;
- `total_expenditure_gdp`: mean 2010-2015 observed expenditure/GDP, then clamped;
- `inflation_target`: mean 2010-2015 inflation, then clamped;
- health/education/infrastructure/transfers/admin/military shares: fixed disclosed split `0.15/0.20/0.20/0.20/0.15/0.10` because historical categories are absent;
- trade policy: `0.0`.

The engine is run from 2015 through the 2024 state, and each target uses absolute relative error with a 20% pass threshold.

Results:

- initialized records: 122;
- records with complete comparable 2024 targets: 113;
- passed all five targets: 0;
- passed four targets: 2;
- passed three targets: 10;
- passed two targets: 33;
- passed one target: 68.

The closest records were:

- Mongolia (`MNG`): 4/5; GDP-per-capita error 30.9%, inflation 11.1%, unemployment 15.2%, debt/GDP 17.5%, life expectancy 0.2%.
- Namibia (`NAM`): 4/5; GDP-per-capita 11.8%, inflation 86.0%, unemployment 0.03%, debt/GDP 10.7%, life expectancy 8.8%.

No record met the full criterion.

### Kenya proxy result

| Target | Predicted | Observed 2024 | Relative error | Pass |
|---|---:|---:|---:|---|
| GDP per capita | 1,129.83 | 2,132.43 | 47.0% | No |
| Inflation | -0.133% | 4.490% | 103.0% | No |
| Unemployment | 24.623% | 5.487% | 348.8% | No |
| Debt/GDP | 300.0% | 67.3% | 345.8% | No |
| Life expectancy | 63.339 | 63.834 | 0.8% | Yes |

The debt ratio reaches the model's 3.0 state ceiling in this proxy. This result is reported rather than tuned away.

## Interpretation of calibration failure

The proxy failure can reflect both model misspecification and measurement mismatch. Material limitations include:

- current-USD GDP compared with a real-growth equation;
- missing exchange-rate and complete GDP-deflator channels;
- fixed spending categories instead of historical categories;
- globally fixed V1 coefficients rather than country-fitted Okun and NKPC parameters;
- no random or historical external-shock sequence;
- no financial sector, resource module, regime type, or bilateral trade;
- nearest-observation baseline fallback for sparse fields.

These limitations do not justify changing coefficients silently. Calibration improvement requires a versioned specification amendment, better country-level inputs, or the V1.5 calibration work described by the roadmap.

## Verification conclusion

The software implementation is internally testable, deterministic, packaged, and consistent with the documented V1 equations and architectural reconciliations. The empirical calibration success criterion is not met or demonstrable with the available data. Researchers should treat POLITY V1 as a transparent model implementation and calibration research platform, not as a validated forecasting system.
