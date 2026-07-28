# Release scripts

## `verify_release.py`

Runs release-level deterministic checks:

- attempts 2015 initialization for every code record;
- runs each successful state for 20 years;
- repeats a canonical Kenya path and checks exact equality;
- verifies input-state immutability;
- emits optional JSON.

```bash
python scripts/verify_release.py --output results/release_verification.json
```

## `security_scan.py`

Scans the worktree and optionally every Git commit for secrets, personal paths, sensitive filenames, binary metadata, caches, backups, and other publication-risk artifacts.

```bash
python scripts/security_scan.py
python scripts/security_scan.py --history
```

The scanner prints only finding categories and locations, never candidate secret values.
