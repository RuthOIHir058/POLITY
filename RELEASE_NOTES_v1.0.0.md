# POLITY Engine v1.0.0 Release Notes

POLITY v1.0.0 is the first publication-ready implementation of the deterministic V1 political-economy engine.

## Highlights

- Complete 24-phase annual update sequence from the authoritative guidebook.
- Immutable prior-year state transition with exact deterministic replay.
- Full causal audit entries for persistent, derived, and reference outputs.
- Five-layer modular architecture covering policy, governance, politics, economy, society, trade, and explicit external shocks.
- Country initialization from a bundled, verified SQLite warehouse.
- CLI, JSON policies, CSV exports, Python API examples, data tooling, CI, and publication documentation.
- 60 passing automated tests and 93 percent branch-aware coverage.
- 122 countries initialized at 2015 and completed a 20-year release run.

## Scientific status

The software implementation is complete, but historical calibration is not.

The exact guidebook 2025 test cannot be run because no country in the bundled warehouse has all five required 2025 observations. In the documented 2015-to-2024 proxy, zero of 113 comparable countries passed all five +/-20 percent targets. Mongolia was closest at four of five. Kenya passed life expectancy only and missed GDP per capita, inflation, unemployment, and debt/GDP.

No coefficient or equation was changed to hide this result. See [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md) and the detailed proxy artifacts in `docs/verification/`.

## Reproducibility

- Supported Python: 3.11, 3.12, and 3.13.
- Core runtime dependencies: none outside the standard library.
- Publication database SHA-256: `6dfd602f35a2cec9309c09d5073059e6a7b9041c6e5ff2cea17e25476b4a79d6`.
- Kenya 2015, 20-year canonical result fingerprint: `991843772a64d354addc4496c5e493c295a946fbf0e9cf45cd912ed6a5008d22`.
- Release tag: `v1.0.0`.

## Security and cleanup

The original tree and archive were scanned before publication. No API keys, tokens, passwords, private keys, cloud credentials, OAuth material, cookies, sessions, or database credentials were found. A raw workbook contained a local workstation path in embedded metadata; raw downloads were excluded. Caches, backup snapshots, obsolete schema scripts, scratch files, and runtime artifacts were removed.

The clean working tree and complete Git history passed the final security scan before the publication decision.

## License status

No license has been selected. `LICENSE_PENDING.md` is not a license grant. Review it before using or redistributing the source or data.

## Upgrade notes

This is the first tagged release. The publication state contract is incompatible with the warehouse-shaped prototype. Downstream code should initialize countries through `initialize_country()` and use canonical decimal ratios rather than raw percentage fields.

## Verification commands

```bash
python -m pip install -r requirements-dev.txt
python -m coverage run --branch -m pytest
python -m coverage report --fail-under=90
python -m tools.validation.check_database_sync
python -m tools.validation.check_determinism --years 20
python scripts/verify_release.py
python scripts/security_scan.py --root . --history
```

See [CHANGELOG.md](CHANGELOG.md) for the full change inventory.
