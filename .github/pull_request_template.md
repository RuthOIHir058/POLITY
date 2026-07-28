## Summary

Describe the problem, mechanism, and implementation.

## Specification and architecture

- Specification section or authorizing issue:
- State/unit/sequencing implications:
- Scientific coefficients changed: yes/no

## Verification

- [ ] `python -m compileall -q engine examples tools scripts main.py`
- [ ] `coverage run --branch -m pytest`
- [ ] `coverage report --fail-under=90`
- [ ] database checks relevant to this change
- [ ] exact determinism check
- [ ] `python scripts/security_scan.py --root .`

Report test count, coverage, deterministic impact, and any calibration/proxy change.

## Documentation

- [ ] public API/CLI documentation updated
- [ ] architecture/implementation report updated when needed
- [ ] verification limitations disclosed
- [ ] changelog updated

## Publication hygiene

- [ ] no credentials, personal paths, raw downloads, caches, logs, backups, or local outputs
- [ ] no failed result hidden or replaced by an undocumented heuristic
