# Contributing to POLITY

POLITY welcomes reproducible bug fixes, tests, documentation, data-quality improvements, and carefully specified model work. Scientific transparency takes priority over feature speed.

## Before contributing

Read:

- `docs/specification/POLITY_ENGINE_V1_SPEC.md`;
- `ARCHITECTURE.md`;
- `IMPLEMENTATION_REPORT.md`;
- `VERIFICATION_REPORT.md`;
- `SECURITY.md`;
- `LICENSE`.

POLITY is released under the MIT License. By submitting a contribution, you agree that your contribution will be licensed under the same MIT License as the project. You represent that you have the legal right to submit your contribution.

## Development setup

```bash
git clone https://github.com/RuthOlHir058/POLITY.git
cd POLITY
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pytest
```

Windows PowerShell activation is `.venv\Scripts\Activate.ps1`.

Install `requirements-data.txt` only when working on downloads or ETL.

## Branch workflow

Use a focused branch created from the current default branch:

```bash
git switch main
git pull --ff-only
git switch -c fix/descriptive-name
```

Recommended prefixes:

- `fix/` for defects;
- `feat/` for approved features;
- `docs/` for documentation;
- `test/` for verification work;
- `data/` for acquisition, ETL, or snapshot work;
- `chore/` for release and maintenance changes.

Do not rewrite shared branch history or force-push over another contributor's work.

## Scientific-change rules

A change to an equation, coefficient, threshold, lag, state variable, update order, calibration rule, or stabilizer is not an ordinary refactor.

Such a pull request must include:

1. the exact guidebook section affected;
2. a clear statement of whether the change fixes non-compliance or proposes a specification amendment;
3. the old and new equations or constants;
4. a causal explanation;
5. unit and range analysis;
6. regression tests for normal, boundary, and failure cases;
7. determinism evidence;
8. calibration impact, including failures;
9. updates to architecture, implementation, verification, and changelog documentation.

Do not replace a specified equation with a heuristic because it produces more attractive output. Do not tune coefficients silently to pass one country.

## Code style

Use:

- Python 3.11-compatible syntax;
- four-space indentation;
- type annotations on public functions and data contracts;
- docstrings for public modules, classes, and non-obvious functions;
- immutable/frozen update records where practical;
- descriptive mechanism names rather than unexplained abbreviations;
- centralized constants instead of new magic numbers;
- pure domain functions that do not mutate caller-owned state;
- explicit finite-value and range validation at boundaries.

Keep lines readable and follow standard PEP 8 conventions. `.editorconfig` defines basic whitespace behavior. The project does not currently require a particular autoformatter; avoid unrelated reformatting in focused changes.

## Architecture boundaries

- `engine/core/` owns contracts, constants, initialization, and orchestration.
- Domain equation packages must not import the CLI.
- Data acquisition and ETL belong under `tools/`, not in annual simulation execution.
- The loader returns source units; initialization performs canonical conversion.
- Tier-3 reference metrics must never feed back into the model.
- New random behavior is out of scope for V1 and requires seeded reproducibility in a later version.

## Testing requirements

Run before every pull request:

```bash
python -m coverage erase
python -m coverage run --branch -m pytest
python -m coverage report --fail-under=90
python -m compileall -q engine tools examples scripts main.py
python -m tools.validation.check_schema
python -m tools.validation.check_loader_contract
python -m tools.validation.check_database_sync
python -m tools.validation.check_determinism --years 20
python scripts/security_scan.py
```

Changes to initialization or the database should also run:

```bash
python scripts/verify_release.py
python -m tools.validation.historical_calibration_proxy
```

A test should assert behavior, not print output for manual inspection. Include failure-path tests for validation and missing data.

## Determinism

New code must not depend on:

- unordered external data traversal;
- wall-clock time;
- process identifiers;
- implicit randomness;
- network responses during a simulation;
- mutable module-level state.

When randomness is introduced in a future release, it must be explicit, seeded, serialized, and replayable.

## Data contributions

Do not commit raw downloads automatically. Before adding or replacing a data snapshot:

- review upstream terms and citation requirements;
- inspect document and archive metadata;
- scan for personal paths, authors, comments, hidden sheets, and credentials;
- run SQLite integrity and schema checks;
- document source versions and transformations;
- update checksums and provenance documents;
- retain missing-data limitations;
- avoid presenting projections as observations.

The two published database copies must remain byte-identical.

## Commit conventions

Use concise conventional-style messages:

```text
fix(engine): preserve prior-year trade ordering
feat(cli): add complete policy-file support
test(governance): cover conflict degradation boundary
docs: explain calibration proxy limitations
chore(release): prepare v1.0.1
```

Use the body to explain why a non-obvious change is necessary. Do not include secrets, personal paths, generated logs, or private issue content in commit messages.

## Pull requests

A pull request should:

- solve one coherent problem;
- explain the previous behavior and the proposed behavior;
- identify scientific impact;
- include tests and documentation;
- report exact verification commands and results;
- disclose failed checks or calibration regressions;
- avoid unrelated formatting or dependency churn;
- pass the security scanner.

Suggested checklist:

```text
[ ] I read the specification and architecture documents.
[ ] I did not change scientific equations without documenting the change.
[ ] I added or updated assertion-based tests.
[ ] The full test suite and coverage floor pass.
[ ] Determinism and input immutability pass.
[ ] Data and loader checks pass where relevant.
[ ] I documented limitations and failed calibration honestly.
[ ] I ran the publication security scan.
[ ] I included no credential, personal path, cache, raw workbook, or runtime output.
```

## Review priorities

Reviewers should evaluate, in order:

1. specification compliance;
2. unit and state-boundary correctness;
3. update ordering and prior-year semantics;
4. determinism and mutation safety;
5. causal audit completeness;
6. tests and failure handling;
7. empirical and data limitations;
8. readability and packaging.

## Issues and discussions

Use issues for reproducible bugs, documentation gaps, and narrowly scoped proposals. Include minimal data needed to reproduce a problem. Never post credentials, personal records, proprietary source files, or private security details.

Use the private security process described in `SECURITY.md` for vulnerabilities.
