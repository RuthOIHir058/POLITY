# Raw data downloads

Raw source downloads are intentionally excluded from version control. The release includes the processed, read-only simulation snapshot at `data/database/polity.db` and acquisition/ETL source under `tools/`.

This exclusion prevents redistribution of source workbooks with embedded author or workstation metadata, keeps generated files out of Git, and avoids implying that third-party source material is covered by a future POLITY software license.

Install optional data dependencies with:

```bash
python -m pip install -r requirements-data.txt
```

Then run acquisition modules from the repository root. Review `tools/download/download_manifest.md` and `docs/data/DATA_PROVENANCE.md` before rebuilding.
