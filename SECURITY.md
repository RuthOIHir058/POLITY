# Security Policy

## Supported version

Security fixes are accepted for the latest `1.0.x` release line. Older development snapshots are not supported.

## Report a vulnerability

After the repository is hosted on GitHub, use the repository's private **Report a vulnerability** or Security Advisory workflow when available. Do not place exploit details, credentials, private data, or proof-of-concept secrets in a public issue.

If private reporting is not enabled, open a minimal public issue asking the maintainer to enable a private channel. Include no sensitive details in that issue.

## What to include privately

A useful report contains:

- the affected release or commit;
- the affected file or component;
- impact and realistic threat model;
- reproducible steps using non-sensitive test data;
- suggested mitigation, if known.

Never send a real API key, password, private key, session cookie, personal record, or credential-bearing database as evidence.

## Repository security rules

Contributors must not commit:

- `.env` files or local configuration containing secrets;
- access tokens, API keys, passwords, OAuth credentials, or cloud credentials;
- SSH/private keys, certificates with private material, or VPN configurations;
- personal email addresses, phone numbers, local user paths, or private network addresses;
- browser profiles, cookies, sessions, IDE metadata, caches, logs, or virtual environments;
- raw vendor workbooks without metadata and redistribution review.

Run before a pull request:

```bash
python scripts/security_scan.py
```

Maintainers must run before a release or push of rewritten history:

```bash
python scripts/security_scan.py --history
```

## Dependency security

The core engine has no third-party runtime dependency. Development and data-tool dependencies are pinned in `requirements-dev.txt` and `requirements-data.txt`. Dependabot configuration is included for pip and GitHub Actions updates.

Dependency updates must pass all tests, coverage, database validation, deterministic fingerprints, and release security scans. A version change must not be merged solely because it is newer.

## Model-integrity issues

Incorrect equations, altered coefficients, broken update ordering, nondeterminism, or audit-log omissions are scientific-integrity defects. Report them through an issue or pull request unless they also create a security impact. Any equation change requires an explicit specification update and regression tests.
