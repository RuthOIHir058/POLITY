# Data sources

The bundled warehouse was assembled from public statistical sources. Source files are not redistributed in this repository; acquisition and ETL scripts document the endpoints and indicator mappings.

| Provider | Main indicators | Acquisition code |
|---|---|---|
| World Bank API | Country metadata, GDP, GDP per capita, inflation, unemployment, population, population growth, urban share, cohort shares, life expectancy, Gini, school-life expectancy, exports, imports | `tools/download/download_world_bank.py` and indicator scripts |
| Worldwide Governance Indicators through World Bank endpoints | Government effectiveness, rule of law, political stability | `tools/download/download_wgi.py` |
| IMF DataMapper | Debt/GDP, revenue/GDP, expenditure/GDP, current account/GDP | `tools/download/download_imf_fiscal.py` |
| Transparency International | Corruption Perceptions Index | `tools/download/download_cpi.py` |
| UNDP Human Development Reports | HDI, mean years of schooling, expected years of schooling | `tools/download/download_undp_hdi.py` |

Each provider retains its own terms. Inclusion of a processed value does not relicense source data. Rebuilding later may produce different observations because public datasets are revised.
