# Data and validation tools

`tools/` is outside the annual simulation path.

## Download tools

`tools/download/` contains credential-free acquisition scripts for the public source systems described in `data/SOURCES.md`. Install optional dependencies with:

```bash
python -m pip install -r requirements-data.txt
```

Raw output belongs under `data/raw/` and is ignored by Git. Inspect metadata and source terms before retaining or redistributing downloads.

## ETL tools

`tools/etl/` contains schema and loader scripts that normalize source data into the four-table SQLite warehouse. These scripts are for controlled snapshot rebuilds, not for simulation-time network access.

## Validation tools

Common release checks include:

```bash
python -m tools.validation.check_schema
python -m tools.validation.check_year_ranges
python -m tools.validation.check_country_coverage
python -m tools.validation.check_missing_data
python -m tools.validation.check_loader_contract
python -m tools.validation.check_database_sync
python -m tools.validation.check_determinism --years 20
python -m tools.validation.historical_calibration_proxy
```

Validation tools fail loudly on contract violations. `check_missing_data` is diagnostic and prints null rates; it does not fill missing values.
