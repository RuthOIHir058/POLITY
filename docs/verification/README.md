# Verification Artifacts

This directory contains publication evidence that is small, deterministic, and safe to review in Git.

- `release_verification.json`: machine-readable 20-year initialization, execution, determinism, immutability, and Kenya summary results.
- `historical_calibration_proxy.txt`: human-readable 2015-to-2024 proxy summary.
- `historical_calibration_proxy.csv`: per-country predicted values, observed values, relative errors, and pass flags.

These files are evidence for V1.0.0, not general benchmarks. Regenerate them after any scientific, initialization, or database change and review the diff rather than overwriting them automatically.

The proxy is not the unavailable exact 2025 guidebook acceptance test. See [VERIFICATION_REPORT.md](../../VERIFICATION_REPORT.md) for methodology and interpretation.
