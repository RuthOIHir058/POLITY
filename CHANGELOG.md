# Changelog

All notable changes to POLITY are documented in this file.

The format follows Keep a Changelog conventions, and release versions follow Semantic Versioning where practical. Because no software license has yet been selected, publication of source does not imply a particular open-source license.

## [Unreleased]

No changes yet.

## [1.0.0] - 2026-07-28

### Added

- Canonical `CountryState`, `PolicyInputs`, `StepResult`, and `AuditEntry` contracts.
- Central constants and variable registries for all V1 mechanisms.
- Complete deterministic 24-phase annual simulation engine.
- Closed-form demographic, urbanization, human-capital, macroeconomic, fiscal, governance, conflict, inequality, health, schooling, trade, and reference-metric modules.
- Fifteen-year human-capital investment pipeline.
- Named-cause audit entries and variable-specific severity classification.
- Sovereign-pressure and unemployment-safety-net automatic stabilizers.
- Raw SQLite loader, country initialization, unit normalization, missing-value policy, and country-specific calibration.
- Installable `polity` CLI with complete policy controls, JSON policy loading, audit output, and CSV export.
- Beginner, custom-policy, and policy-comparison examples.
- Bundled sanitized SQLite warehouse and byte-identical package copy.
- Schema, range, coverage, loader, database-sync, determinism, full-release, and historical-proxy validation utilities.
- Unit, integration, and subprocess smoke tests.
- Branch-aware coverage configuration with a 90% floor.
- GitHub Actions CI matrix for Python 3.11-3.13 and Dependabot configuration.
- Publication security scanner for worktree and Git history.
- Installation, quick-start, architecture, implementation, verification, security, data-provenance, contribution, and release documentation.

### Changed

- Replaced the warehouse-shaped prototype state with a canonical decimal-unit state boundary.
- Replaced the in-place prototype step function with immutable prior-state execution.
- Replaced incorrect or incomplete GDP, conflict, output-gap, inflation, unemployment, debt, risk, capacity, and initialization behavior with the guidebook equations.
- Converted `SimulationStep` from placeholder code to a compatibility facade.
- Separated download/ETL tooling from the annual simulation package.
- Centralized country initialization and converted source percentages exactly once.
- Added explicit reconciliations for prior conflict risk, prior GDP growth, prospective trade, and Step-23 stabilizer recomputation.

### Removed

- Obsolete `simulation_engine.py` backup and `.pre_*` snapshots.
- Print-only smoke scripts tied to the obsolete state contract.
- Scratch analysis code, generated caches, bytecode, test caches, logs, runtime outputs, and an unused database backup.
- Raw third-party workbooks from the publication tree.

### Security

- Audited all source, hidden files, database text, archive members, OOXML metadata, PNG metadata, binary strings, and final Git history.
- Found no credentials, tokens, private keys, passwords, or cloud authentication material in the release tree.
- Excluded two raw workbooks containing embedded author or local-path metadata.
- Added fail-closed publication scanning and credential-oriented `.gitignore` rules.
- Did not push to GitHub because no secure authenticated session was available.

### Verification

- 60 automated tests pass.
- Branch-aware engine coverage is 93%.
- All shipped Python source compiles.
- Both database copies share SHA-256 `6dfd602f35a2cec9309c09d5073059e6a7b9041c6e5ff2cea17e25476b4a79d6`.
- A canonical repeated 20-year Kenya simulation matches exactly and leaves the input state unchanged.
- 122 code records initialize at 2015 and complete a 20-year simulation; 174 lack one or more required fields.
- The installable wheel runs from outside the source tree using the packaged database.
- The exact guidebook 2025 calibration criterion cannot be executed from available observations.
- The disclosed 2015-2024 proxy has 113 comparable records and zero full five-target passes.

### Known limitations

- Historical category-level expenditure shares are unavailable.
- GDP data are current USD while the model growth equation is real.
- The default global coefficients are not country-fitted.
- The release is not empirically validated as a forecasting system.
- A software license remains pending owner selection.

[Unreleased]: https://github.com/RuthOlHir058/POLITY/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/RuthOlHir058/POLITY/releases/tag/v1.0.0
