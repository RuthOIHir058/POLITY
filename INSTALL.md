# Installation Guide

This guide installs POLITY Engine V1.0.0 from a Git clone. The core simulator has no third-party runtime dependencies, but the development profile installs the pinned test and coverage tools used for release verification.

## Supported Python versions

POLITY supports CPython 3.11, 3.12, and 3.13. Python 3.14 and later have not been verified for this release.

Check the interpreter before creating an environment:

```bash
python --version
```

On systems where `python` is not available, try `python3` on Linux or macOS, or `py` on Windows.

## Clone the repository

Using HTTPS:

```bash
git clone https://github.com/RuthOlHir058/POLITY.git
cd POLITY
```

Using SSH after GitHub SSH authentication has already been configured:

```bash
git clone git@github.com:RuthOlHir058/POLITY.git
cd POLITY
```

Do not place credentials in the clone URL, command history, configuration files, or issue reports.

## Windows

### PowerShell

Create a virtual environment with a supported interpreter:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

When local PowerShell policy blocks activation, enable scripts only for the current process and retry:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Verify the installation:

```powershell
polity --version
python -m pytest
python -m coverage run --branch -m pytest
python -m coverage report --fail-under=90
```

Run a simulation:

```powershell
polity KEN --start-year 2015 --years 20 --policy-file configs\baseline_policy.json --output results\kenya.csv
```

### Command Prompt

```bat
py -3.13 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
polity KEN --start-year 2015 --years 5
```

## Linux

Install Python, virtual-environment support, and Git using your operating system's package manager. Package names differ by distribution. Then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Verify and run:

```bash
polity --version
python -m pytest
python -m tools.validation.check_schema
polity KEN --start-year 2015 --years 20 --output results/kenya.csv
```

When `python3 -m venv` reports that the venv module is unavailable, install the distribution package that provides Python virtual environments, then recreate `.venv`.

## macOS

Use a supported Python installation rather than the system-provided interpreter. After Python and Git are available:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Verify and run:

```bash
polity --version
python -m pytest
polity KEN --start-year 2015 --years 20 --policy-file configs/baseline_policy.json
```

On Apple Silicon and Intel macOS, the core engine remains pure Python. Optional data tools use binary wheels where available; if optional installation fails, the core engine can still be installed with `requirements.txt`.

## Installation profiles

### Core simulation only

```bash
python -m pip install -r requirements.txt
```

This installs POLITY in editable mode and provides the `polity` command. It does not install tests or data-rebuild dependencies.

### Development and verification

```bash
python -m pip install -r requirements-dev.txt
```

Pinned packages:

- `pytest==9.0.2`
- `coverage==7.13.3`

### Data acquisition and ETL

```bash
python -m pip install -r requirements-data.txt
```

This adds:

- `requests==2.32.5`
- `pandas==2.2.3`
- `openpyxl==3.1.5`

Raw data is intentionally not committed. See [docs/data/DATA_PROVENANCE.md](docs/data/DATA_PROVENANCE.md) before rebuilding the warehouse.

## Run the tests

Fast test run:

```bash
python -m pytest
```

Release coverage run:

```bash
python -m coverage erase
python -m coverage run --branch -m pytest
python -m coverage report --fail-under=90
```

Publication checks:

```bash
python -m compileall -q engine tools examples scripts main.py
python -m tools.validation.check_schema
python -m tools.validation.check_loader_contract
python -m tools.validation.check_database_sync
python -m tools.validation.check_determinism --years 20
python scripts/verify_release.py
python scripts/security_scan.py --root .
```

## Run simulations

Display a baseline simulation:

```bash
polity KEN --start-year 2015 --years 20
```

Use a complete policy file:

```bash
polity KEN --start-year 2015 --years 20 \
  --policy-file configs/education_infrastructure_reform.json
```

Override selected policy fields:

```bash
polity KEN --start-year 2015 --years 20 \
  --policy-file configs/baseline_policy.json \
  --tax-rate 0.38 \
  --trade-policy 0.25
```

Save CSV and show material audit events:

```bash
polity KEN --start-year 2015 --years 20 \
  --audit \
  --output results/kenya.csv
```

## Database selection

By default, a source checkout uses `data/database/polity.db`. A packaged installation can fall back to the byte-identical copy in `engine/data/polity.db`.

Use a different compatible warehouse with:

```bash
polity KEN --database path/to/polity.db --start-year 2015 --years 20
```

The database must match [docs/data/schema_reference.sql](docs/data/schema_reference.sql). Validate it before simulation:

```bash
python -m tools.validation.check_schema --database path/to/polity.db
```

## Common errors and troubleshooting

### `polity` is not recognized or not found

The virtual environment may not be active, or the editable installation may not have completed. Activate `.venv`, then run:

```bash
python -m pip install -r requirements.txt
python -m engine.cli --version
```

`python -m engine.cli` is a direct fallback for the console script.

### Unsupported Python version

Create a fresh virtual environment with Python 3.11, 3.12, or 3.13. Reusing an environment created by another interpreter can produce misleading import errors.

### Database not found

Confirm that `data/database/polity.db` exists in a source checkout. When using `--database`, verify the spelling and that the current user can read the file.

### Unknown country code

Country codes use uppercase ISO3-like identifiers in the warehouse. The CLI normalizes case, but a code must exist in the `countries` table.

### Country cannot initialize

A country record may lack one or more required historical values. The initializer searches for the nearest same-country observation, preferring an earlier year when distances tie, but it fails rather than silently inventing a required field. The release verification finds 122 countries that can initialize at 2015 and 174 that cannot.

### Expenditure shares do not sum to 1.0

The six expenditure shares must sum to 1.0 within 0.001. They divide total expenditure; they are not separate GDP fractions.

### Policy value outside range

The validator enforces the guidebook bounds, including tax rate 0.05 to 0.55, total expenditure 0.10 to 0.65, and trade policy -1 to 1. Correct the JSON or command-line override instead of bypassing validation.

### CSV cannot be written

Choose a writable destination. Parent directories are created automatically, but the process still needs permission to create files at the selected location.

### Optional data package installation fails

The simulation does not require optional data packages. Install the core or development profile first. Use the data profile only when running download or ETL modules.

### Test results differ from the release report

Confirm the tag, Python version, database checksum, policy file, and working tree status. Remove generated caches, reinstall the pinned development profile, and rerun the exact commands in [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md).

## Uninstall or reset

Because the project is installed in editable mode, uninstall it with:

```bash
python -m pip uninstall polity-engine
```

Then deactivate the environment and remove `.venv` using the normal file-management tools for your operating system. Generated `results/` and cache directories are ignored by Git.
