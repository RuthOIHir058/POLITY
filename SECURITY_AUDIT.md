# POLITY V1 Publication Security Audit

**Audit date:** 2026-07-28  
**Release:** 1.0.0  
**Scope:** original handoff, implementation working tree, cleaned publication tree, packaged database, binary metadata, and final Git history

## Executive summary

No API key, access token, password, OAuth credential, private key, cloud credential, database connection secret, cookie, session identifier, VPN profile, personal email address, phone number, or internal network address was found in the publishable POLITY source.

The original handoff did contain publication-risk metadata in third-party spreadsheet files: one workbook embedded a local Windows user-directory path, and the workbooks contained third-party document creator/last-modifier names. Those raw workbooks and all other raw downloads were excluded from the public repository. Acquisition and ETL source code remains, and the processed SQLite snapshot was separately inspected.

The working tree also contained generated caches, obsolete backups, scratch code, and an unused backup database. Those files were removed before Git history was created.

GitHub authentication was not available in the release-preparation environment. No credential was requested, created, copied, or stored, and no network push was attempted. Publication commands are documented in [PUBLISHING.md](PUBLISHING.md).

## Audit method

The audit combined automated and manual inspection. The automated scanner is [`scripts/security_scan.py`](scripts/security_scan.py), implemented with the Python standard library so it can run in an offline clean checkout.

### File and directory inventory

The original implementation working tree contained:

```text
256 files
71,889,517 bytes
```

The inventory included visible and hidden files, source, Markdown, TOML, JSON, SQL, raw downloads, SQLite databases, workbooks, Python bytecode, test caches, backups, and temporary implementation snapshots. It identified more than one hundred cache, backup, raw-download, scratch, and temporary artifacts before publication staging.

The review searched for:

- hidden environment/configuration files;
- cloud, SSH, GPG, browser, VPN, and credential-manager paths;
- virtual environments and package caches;
- IDE/editor metadata;
- OS metadata;
- logs, runtime outputs, and temporary files;
- backup and pre-change snapshots;
- symlinks and special files;
- world-writable or unexpected executable files.

### Secret and credential patterns

Every text-like file was scanned line by line for:

- AWS access-key formats;
- GitHub and GitLab token formats;
- OpenAI, Anthropic, Hugging Face, Google, Slack, and Stripe key formats;
- JSON Web Tokens;
- private-key and certificate headers;
- credentialed URLs;
- Azure-style account connection strings;
- generic API-key, secret, token, password, session, cookie, connection-string, and database-URL assignments.

The scanner reports only category, location, and line number; it does not print candidate secret values.

### Personal and local information patterns

Text and binary strings were checked for:

- personal email addresses, excluding GitHub no-reply identities;
- Windows, macOS, Linux, root, temporary-workspace, and staging paths;
- private IPv4 address ranges;
- international phone-number patterns;
- local usernames embedded in file metadata or paths.

### Binary inspection

Binary files were not treated as opaque:

- SQLite schemas and every text-valued cell were queried in read-only mode and scanned.
- OOXML/ZIP members were enumerated; XML, relationships, text, JSON, CSV, and VML members were decoded and scanned.
- PNG `tEXt`, `zTXt`, and `iTXt` chunks were inspected.
- Printable strings from other unknown binary formats were scanned.
- Archive member names were checked for sensitive filenames.

### Source-code risk review

Source files were manually and automatically checked for:

- `eval`/dynamic execution patterns;
- unsafe object deserialization;
- shell execution with untrusted interpolation;
- `shell=True` use;
- disabled TLS verification;
- embedded authentication headers or credentials;
- hidden network calls in the simulation core;
- environment-variable dependence in deterministic equations.

No such issue was found in the V1 simulation core. Download tools use explicit public-source URLs and no credentials.

### Database review

Both database copies were checked for:

- SQLite integrity and foreign-key errors;
- text-cell secret/PII patterns;
- schema content;
- exact byte identity;
- transient journal/WAL side files.

No sensitive text was found in the database. No journal, WAL, or shared-memory file is included. The two release copies are byte-identical with SHA-256:

```text
6dfd602f35a2cec9309c09d5073059e6a7b9041c6e5ff2cea17e25476b4a79d6
```

### Authentication and publication environment review

Before considering a GitHub operation, the environment was checked for:

- GitHub CLI authentication;
- GitHub-related environment tokens;
- Git credential-store files;
- configured Git credential helpers;
- SSH keys and SSH configuration;
- usable GitHub remotes.

No GitHub authentication material was available. This is the safe stopping condition required by the publication instructions.

## Findings

### Critical or high-severity secrets

**None found.**

No credential rotation was necessary because no credential value was discovered.

### Publication-risk metadata

Two raw workbooks contained document metadata not needed to run POLITY:

1. A corruption-index workbook embedded a local Windows user-directory path and third-party creator/modifier metadata.
2. A human-development workbook embedded third-party creator/modifier metadata and SharePoint/local-path metadata.

The workbook contents were not copied into repository documentation. The files were excluded in full rather than attempting to strip and redistribute them.

### False-positive review

Binary string searches can resemble email addresses or key material by chance. Candidate SQLite strings were checked against table context; none represented personal email or credentials. Pattern definitions inside the scanner are constructed to avoid self-triggering where possible, and final findings were manually reviewed by category and location.

## Removed or excluded items

### Sensitive or privacy-relevant exclusions

- `data/raw/cpi/cpi_2024.xlsx` — excluded because of embedded local workstation and author metadata.
- `data/raw/undp/hdi_2025.xlsx` — excluded because of embedded third-party author metadata.
- All other files under the original `data/raw/` tree — excluded to avoid redistributing third-party source downloads under an unspecified project license and to prevent overlooked source metadata.

The public tree retains `data/raw/README.md`, acquisition scripts, ETL scripts, source notes, and the processed release snapshot.

### Generated and local artifacts removed

- all `__pycache__/` directories;
- all `*.pyc` bytecode;
- `.pytest_cache/`;
- `.coverage`;
- generated package metadata and build directories;
- local result/output directories and logs;
- editor swap/backup patterns covered by `.gitignore`.

### Obsolete or risky development artifacts removed

- `engine/core/simulation_engine.py.bak`;
- `engine/core/simulation_engine.py.pre_macro`;
- `engine/core/simulation_engine.py.pre_inflation`;
- `engine/core/simulation_engine.py.pre_fiscal`;
- `scratch_ilo_test.py`;
- `data/database/polity_backup_v1.db`;
- superseded schema/init/seed experiments;
- empty out-of-scope placeholder packages for pre-V1.5/V2 mechanisms;
- stale architecture/data documents replaced by the release documentation.

These files were removed before the repository's initial commit, so they are not present in the prepared Git history.

## Publication controls added

### `.gitignore`

The release ignores:

- virtual environments;
- Python, test, type-check, and lint caches;
- build and package outputs;
- coverage files;
- logs and runtime outputs;
- SQLite journals/WAL files;
- raw downloads other than their README;
- environment and credential files;
- private keys, certificates, and VPN profiles;
- IDE/editor metadata;
- notebook checkpoints;
- OS metadata;
- backup and temporary files.

### GitHub Actions hardening

The CI workflow:

- requests read-only repository contents permission;
- disables persisted checkout credentials;
- runs the security scanner on the pristine checkout before dependency installation creates caches or package metadata;
- installs only declared project and test dependencies;
- runs compilation, tests, coverage, database checks, and determinism checks.

### Package minimization

The built wheel contains only the simulation package, CLI compatibility module, entry-point metadata, and packaged SQLite snapshot. Repository-only tests, raw-data tooling, documentation, caches, and local outputs are not installed as runtime package content. It contains no `License` or `License-File` metadata because no license has been selected; `LICENSE_PENDING.md` remains a source-repository and source-distribution notice rather than being presented as a package license.

The wheel extraction passed the format-aware scanner with zero findings. The source distribution was also inspected: its six standard generated `*.egg-info` text files produced zero secret or personal-information findings, and the remaining extracted source tree passed the full scanner with zero findings.

### Security reporting

[`SECURITY.md`](SECURITY.md) directs reporters to GitHub's private security-reporting workflow and prohibits public disclosure of credentials or sensitive samples.

## Final scan protocol and result

Immediately before each release-preparation commit, the full working tree is scanned:

```bash
python scripts/security_scan.py --root .
```

After Git commits are created, every reachable committed text blob is also scanned, while the current copies of binary assets are scanned through their format-aware handlers:

```bash
python scripts/security_scan.py --root . --history
```

The clean pre-commit publication tree contained 167 files and produced zero findings. After the five logical commits and annotated release tag were created, the full tree plus every reachable commit also produced zero findings. Generated test, coverage, build, and package files were removed before scanning; their presence is treated as a release failure rather than silently ignored.

## Residual risk and limits

No finite pattern scan can prove that every possible encoded or steganographic secret is absent. Residual risk is reduced by combining source review, filename inspection, archive metadata inspection, SQLite queries, binary-string scanning, a minimal wheel, a clean Git history, and no authenticated push from the preparation environment.

The processed database contains country-level public statistical indicators. It does not contain individual-level records, but source licensing and statistical revision risk remain. The repository does not claim that the pending project license covers third-party data.

The acquisition tools download remote content. A future data refresh should validate response status, provenance, schema, metadata, and hashes before replacing the reference snapshot.

## Audit outcome

**Approved for owner-authenticated publication. The preparation environment had no GitHub authentication, so the secure deliverable stops at a clean tagged repository and exact publication commands.**
