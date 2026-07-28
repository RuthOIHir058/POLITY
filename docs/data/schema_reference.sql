-- POLITY Authoritative Warehouse Schema
-- Source of truth: data/database/polity.db

CREATE TABLE countries (
    iso3 TEXT PRIMARY KEY,
    country_name TEXT NOT NULL,
    region TEXT,
    income_group TEXT
);

CREATE TABLE economic_indicators (
    iso3 TEXT NOT NULL,
    year INTEGER NOT NULL,

    gdp_current_usd REAL,
    gdp_per_capita REAL,
    inflation REAL,

    debt_gdp REAL,
    revenue_gdp REAL,
    expenditure_gdp REAL,

    unemployment REAL,
    current_account_gdp REAL,

    exports_gdp REAL,
    imports_gdp REAL,
    trade_openness REAL,

    PRIMARY KEY (iso3, year)
);

CREATE TABLE governance_indicators (
    iso3 TEXT NOT NULL,
    year INTEGER NOT NULL,

    government_effectiveness REAL,
    rule_of_law REAL,
    corruption_index REAL,
    political_stability REAL,

    PRIMARY KEY (iso3, year)
);

CREATE TABLE societal_indicators (
    iso3 TEXT NOT NULL,
    year INTEGER NOT NULL,

    life_expectancy REAL,
    gini REAL,

    population REAL,
    population_growth REAL,
    urban_population_pct REAL,

    youth_share REAL,
    working_age_share REAL,
    elderly_share REAL,

    hdi REAL,
    expected_years_schooling REAL,
    mean_years_schooling REAL,

    school_life_expectancy REAL,

    PRIMARY KEY (iso3, year)
);
