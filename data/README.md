# POLITY data layout

The release includes one processed SQLite snapshot in two byte-identical locations:

- `data/database/polity.db` — used from a source checkout.
- `engine/data/polity.db` — packaged fallback used after wheel installation.

Verify the checked-in source snapshot from the repository root:

```bash
cd data/database
sha256sum -c SHA256SUMS
```

On Windows PowerShell, compare `Get-FileHash polity.db -Algorithm SHA256` with the value in `SHA256SUMS`. Run `python -m tools.validation.check_database_sync` to confirm that the source and packaged copies are byte-identical.

Raw third-party downloads are intentionally excluded. See `data/raw/README.md`, `data/SOURCES.md`, and `docs/data/DATA_PROVENANCE.md`.
