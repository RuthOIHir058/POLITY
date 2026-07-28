# Data acquisition manifest

The bundled SQLite snapshot is sufficient to run the V1 engine. These scripts
rebuild the raw acquisition layer from public statistical endpoints; they do
not require API keys, cookies, or credentials.

| Source | Indicators | Script |
|---|---|---|
| World Bank API | GDP, GDP per capita, inflation, unemployment, population, population growth, urban share, cohort shares, life expectancy, Gini, school life expectancy, exports and imports | `download_*.py` indicator scripts |
| World Governance Indicators via World Bank API | Government effectiveness, rule of law, political stability | `download_wgi.py` |
| IMF DataMapper | Debt/GDP, revenue/GDP, expenditure/GDP, current account/GDP | `download_imf_fiscal.py` |
| Transparency International | Corruption Perceptions Index 2024 workbook | `download_cpi.py` |
| UNDP | 2025 Human Development Report statistical annex | `download_undp_hdi.py` |

Run scripts as modules from the repository root, for example:

```bash
python -m tools.download.download_world_bank
python -m tools.download.download_gdp
python -m tools.download.download_wgi
```

Remote datasets can be revised after this release. See `docs/data/DATA_PROVENANCE.md`
for snapshot and reproducibility limitations.
