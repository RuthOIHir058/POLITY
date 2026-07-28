# Data provenance and reproducibility

## Release snapshot

POLITY v1.0.0 uses a fixed SQLite snapshot so simulations can be reproduced independently of later upstream revisions.

```text
Path in clone: data/database/polity.db
Packaged fallback: engine/data/polity.db
SHA-256: 6dfd602f35a2cec9309c09d5073059e6a7b9041c6e5ff2cea17e25476b4a79d6
```

The copies must remain byte-identical.

## Sources

The warehouse combines:

- World Bank API indicator series and country metadata;
- Worldwide Governance Indicators exposed through World Bank endpoints;
- IMF DataMapper fiscal series;
- Transparency International CPI data;
- UNDP Human Development Report tables.

Exact acquisition endpoints and indicator identifiers are encoded in `tools/download/`. Transformation logic is under `tools/etl/`. The schema is preserved at `docs/data/schema_reference.sql`.

## Units

Warehouse values retain source-style units. In particular, many macroeconomic and population-share fields are percentages. `initialize_country` converts these to decimal ratios exactly once when constructing `CountryState`.

GDP is historical current USD. The V1 engine updates GDP using a real-growth equation. This mismatch is material for historical calibration and is disclosed in `VERIFICATION_REPORT.md`.

## Missing data

The warehouse is not balanced. Governance, inequality, fiscal, and schooling fields are especially sparse. Initialization first uses the requested baseline value, then a nearest same-country observation for a missing required field. Equal-distance ties prefer the earlier year. If a required field has no observation for that country, initialization fails explicitly.

The validator `python -m tools.validation.check_missing_data` reports null rates without filling them.

## Education and military history

Historical category-level education and military expenditure are not available in the snapshot. The human-capital queue uses the guidebook's 4%-of-GDP education fallback. Conflict-intercept calibration uses a zero military baseline. These are documented implementation reconciliations, not inferred historical observations.

## Corruption scale

The guidebook describes WGI Control of Corruption, but the available corruption source is CPI on a 0–100 scale. The initializer detects the input range: WGI-style values use WGI normalization; CPI values use `1 - CPI/100` so 1 remains maximally corrupt.

## Raw source exclusion

Raw downloads are not committed because:

- redistribution terms differ by provider;
- source workbooks contained embedded third-party author and local-workstation metadata;
- current upstream downloads may differ from the release snapshot;
- the processed database is sufficient to run V1.

The release therefore separates **simulation reproducibility** from **full source-data reacquisition**. The former uses the fixed database; the latter requires rerunning acquisition and ETL with appropriate source-term review.

## Rebuild outline

1. Install `requirements-data.txt`.
2. Run acquisition scripts as modules from the repository root.
3. Create the schema with `python -m tools.etl.create_schema` against a new database path.
4. Run the relevant ETL loaders.
5. Execute every validation utility.
6. Compare row counts, missingness, ranges, and model outputs with the release snapshot.
7. Inspect raw archive/workbook metadata before publication.
8. Copy the approved database to both release locations and run the hash-sync check.

There is intentionally no single command that silently overwrites the released database.

## Snapshot validation

The release snapshot passed SQLite integrity and foreign-key checks. Row counts are:

| Table | Rows |
|---|---:|
| countries | 296 |
| economic_indicators | 20,318 |
| governance_indicators | 5,489 |
| societal_indicators | 16,969 |

See `VERIFICATION_REPORT.md` for year ranges, coverage, and calibration limitations.
