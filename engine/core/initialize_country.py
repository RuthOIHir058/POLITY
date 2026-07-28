"""Country calibration and normalization from the historical SQLite warehouse."""

from __future__ import annotations

from collections.abc import Mapping

from engine.core.constants import (
    CAPACITY_MAX,
    CAPACITY_MIN,
    CORRUPTION_MAX,
    CORRUPTION_MIN,
    DEFAULT_EDUCATION_SPEND_GDP,
    DEFAULT_POTENTIAL_GROWTH,
    DEFAULT_STRUCTURAL_UNEMPLOYMENT,
    FISCAL_CAPACITY_REVENUE_REFERENCE,
    GINI_MAX,
    GINI_MIN,
    HC_PIPELINE_LAG,
    HUMAN_CAPITAL_MAX,
    HUMAN_CAPITAL_MIN,
    INFLATION_MAX,
    INFLATION_MIN,
    LIFE_EXPECTANCY_MAX,
    RISK_PREMIUM_MAX,
    RISK_PREMIUM_MIN,
    LIFE_EXPECTANCY_MIN,
    TRADE_OPENNESS_MAX,
    TRADE_OPENNESS_MIN,
    UNEMPLOYMENT_MAX,
    UNEMPLOYMENT_MIN,
    URBANIZATION_CAPACITY_INCREMENT,
    URBANIZATION_CAPACITY_MAX,
)
from engine.core.country_state import CountryState
from engine.core.helpers import clamp, trimmed_mean
from engine.data.country_loader import (
    ConnectionInput,
    load_nearest_value,
    load_range,
    load_year,
)
from engine.economy.fiscal import debt_risk_function
from engine.politics.stability import (
    calibrate_conflict_intercept,
    conflict_risk_from_wgi,
)
from engine.society.human_capital import initialize_hc_pipeline


FIELD_TABLE = {
    "gdp_current_usd": "economic_indicators",
    "inflation": "economic_indicators",
    "unemployment": "economic_indicators",
    "debt_gdp": "economic_indicators",
    "revenue_gdp": "economic_indicators",
    "trade_openness": "economic_indicators",
    "rule_of_law": "governance_indicators",
    "corruption_index": "governance_indicators",
    "political_stability": "governance_indicators",
    "population": "societal_indicators",
    "youth_share": "societal_indicators",
    "working_age_share": "societal_indicators",
    "elderly_share": "societal_indicators",
    "urban_population_pct": "societal_indicators",
    "life_expectancy": "societal_indicators",
    "gini": "societal_indicators",
    "mean_years_schooling": "societal_indicators",
    "expected_years_schooling": "societal_indicators",
}


def normalize_wgi(wgi_score: float) -> float:
    """Map WGI [-2.5, +2.5] to [0, 1]."""

    return clamp((float(wgi_score) + 2.5) / 5.0, 0.0, 1.0)


def compute_education_index(baseline: Mapping[str, object]) -> float:
    """Reproduce the guidebook education index from MYS and EYS."""

    mys_raw = baseline.get("mean_years_schooling", 8.0)
    eys_raw = baseline.get("expected_years_schooling", 12.0)
    mys = 8.0 if mys_raw is None else float(mys_raw)
    eys = 12.0 if eys_raw is None else float(eys_raw)
    return (
        min(mys, 15.0) / 15.0 + min(eys, 18.0) / 18.0
    ) / 2.0


def _ratio_from_percent(value: float) -> float:
    return float(value) / 100.0


def _required_value(
    baseline: Mapping[str, object],
    field: str,
    country_code: str,
    start_year: int,
    db_conn: ConnectionInput,
) -> float:
    value = baseline.get(field)
    if value is not None:
        return float(value)
    table = FIELD_TABLE[field]
    nearest = load_nearest_value(
        db_conn, country_code, table, field, start_year
    )
    if nearest is None:
        raise ValueError(
            f"Cannot initialize {country_code} {start_year}: no historical {field}"
        )
    return nearest


def _normalize_corruption(raw_value: float) -> float:
    """Normalize available WGI or CPI corruption data to 1=maximally corrupt."""

    value = float(raw_value)
    if -2.5 <= value <= 2.5:
        corruption = 1.0 - normalize_wgi(value)
    elif 0.0 <= value <= 100.0:
        corruption = 1.0 - value / 100.0
    else:
        raise ValueError(f"Unsupported corruption index scale: {value}")
    return clamp(corruption, CORRUPTION_MIN, CORRUPTION_MAX)


def _historical_growth_series(
    country_code: str,
    start_year: int,
    db_conn: ConnectionInput,
    historical_window: int,
) -> list[float]:
    rows = load_range(
        db_conn,
        country_code,
        start_year - historical_window - 1,
        start_year - 1,
    )
    by_year = {int(row["year"]): row for row in rows}
    growth: list[float] = []
    for year in range(start_year - historical_window, start_year):
        current = by_year.get(year)
        previous = by_year.get(year - 1)
        if not current or not previous:
            continue
        current_gdp = current.get("gdp_current_usd")
        previous_gdp = previous.get("gdp_current_usd")
        inflation = current.get("inflation")
        if current_gdp is None or previous_gdp is None or inflation is None:
            continue
        nominal_growth = float(current_gdp) / float(previous_gdp) - 1.0
        inflation_ratio = _ratio_from_percent(float(inflation))
        if 1.0 + inflation_ratio <= 0.0:
            continue
        real_growth_proxy = (
            (1.0 + nominal_growth) / (1.0 + inflation_ratio) - 1.0
        )
        growth.append(real_growth_proxy)
    return growth


def _historical_unemployment_series(
    country_code: str,
    start_year: int,
    db_conn: ConnectionInput,
    historical_window: int,
) -> list[float]:
    rows = load_range(
        db_conn,
        country_code,
        start_year - historical_window,
        start_year - 1,
    )
    return [
        _ratio_from_percent(float(row["unemployment"]))
        for row in rows
        if row.get("unemployment") is not None
    ]


def initialize_country(
    country_code: str | CountryState,
    start_year: int | None = None,
    db_conn: ConnectionInput = None,
    historical_window: int = 5,
) -> CountryState:
    """Load and calibrate a country according to Section 10 of the guidebook."""

    if isinstance(country_code, CountryState):
        if start_year is not None:
            raise ValueError("start_year is not used when a CountryState is supplied")
        return country_code.clone()
    if start_year is None:
        raise ValueError("start_year is required")
    if historical_window <= 0:
        raise ValueError("historical_window must be positive")

    code = country_code.upper()
    baseline = load_year(db_conn, code, start_year)

    gdp = _required_value(baseline, "gdp_current_usd", code, start_year, db_conn)
    inflation = clamp(
        _ratio_from_percent(
            _required_value(baseline, "inflation", code, start_year, db_conn)
        ),
        INFLATION_MIN,
        INFLATION_MAX,
    )
    unemployment = clamp(
        _ratio_from_percent(
            _required_value(baseline, "unemployment", code, start_year, db_conn)
        ),
        UNEMPLOYMENT_MIN,
        UNEMPLOYMENT_MAX,
    )
    debt_gdp = clamp(
        _ratio_from_percent(
            _required_value(baseline, "debt_gdp", code, start_year, db_conn)
        ),
        0.0,
        3.0,
    )
    revenue_gdp = _ratio_from_percent(
        _required_value(baseline, "revenue_gdp", code, start_year, db_conn)
    )

    population = _required_value(
        baseline, "population", code, start_year, db_conn
    )
    youth_share = _ratio_from_percent(
        _required_value(baseline, "youth_share", code, start_year, db_conn)
    )
    working_age_share = _ratio_from_percent(
        _required_value(
            baseline, "working_age_share", code, start_year, db_conn
        )
    )
    elderly_share = _ratio_from_percent(
        _required_value(baseline, "elderly_share", code, start_year, db_conn)
    )
    urban_pop_pct = _ratio_from_percent(
        _required_value(
            baseline, "urban_population_pct", code, start_year, db_conn
        )
    )
    life_expectancy = clamp(
        _required_value(
            baseline, "life_expectancy", code, start_year, db_conn
        ),
        LIFE_EXPECTANCY_MIN,
        LIFE_EXPECTANCY_MAX,
    )
    gini = clamp(
        _ratio_from_percent(
            _required_value(baseline, "gini", code, start_year, db_conn)
        ),
        GINI_MIN,
        GINI_MAX,
    )
    trade_openness = clamp(
        _ratio_from_percent(
            _required_value(
                baseline, "trade_openness", code, start_year, db_conn
            )
        ),
        TRADE_OPENNESS_MIN,
        TRADE_OPENNESS_MAX,
    )

    rule_of_law = _required_value(
        baseline, "rule_of_law", code, start_year, db_conn
    )
    corruption_raw = _required_value(
        baseline, "corruption_index", code, start_year, db_conn
    )
    political_stability = _required_value(
        baseline, "political_stability", code, start_year, db_conn
    )

    education_baseline = dict(baseline)
    if education_baseline.get("mean_years_schooling") is None:
        education_baseline["mean_years_schooling"] = _required_value(
            baseline,
            "mean_years_schooling",
            code,
            start_year,
            db_conn,
        )
    if education_baseline.get("expected_years_schooling") is None:
        education_baseline["expected_years_schooling"] = _required_value(
            baseline,
            "expected_years_schooling",
            code,
            start_year,
            db_conn,
        )
    human_capital = clamp(
        compute_education_index(education_baseline),
        HUMAN_CAPITAL_MIN,
        HUMAN_CAPITAL_MAX,
    )

    growth_series = _historical_growth_series(
        code, start_year, db_conn, historical_window
    )
    potential_growth = (
        trimmed_mean(growth_series, trim=0.10)
        if growth_series
        else DEFAULT_POTENTIAL_GROWTH
    )
    unemployment_series = _historical_unemployment_series(
        code, start_year, db_conn, historical_window
    )
    structural_unemployment = clamp(
        min(unemployment_series)
        if unemployment_series
        else DEFAULT_STRUCTURAL_UNEMPLOYMENT,
        UNEMPLOYMENT_MIN,
        UNEMPLOYMENT_MAX,
    )

    urbanization_capacity = min(
        URBANIZATION_CAPACITY_MAX,
        urban_pop_pct + URBANIZATION_CAPACITY_INCREMENT,
    )
    target_conflict_risk = conflict_risk_from_wgi(political_stability)

    state = CountryState(
        country_code=code,
        year=int(start_year),
        gdp=gdp,
        inflation=inflation,
        unemployment=unemployment,
        debt_gdp=debt_gdp,
        risk_premium=clamp(
            debt_risk_function(debt_gdp),
            RISK_PREMIUM_MIN,
            RISK_PREMIUM_MAX,
        ),
        fiscal_capacity=clamp(
            revenue_gdp / FISCAL_CAPACITY_REVENUE_REFERENCE,
            CAPACITY_MIN,
            CAPACITY_MAX,
        ),
        legal_capacity=clamp(
            normalize_wgi(rule_of_law), CAPACITY_MIN, CAPACITY_MAX
        ),
        corruption=_normalize_corruption(corruption_raw),
        population=population,
        youth_share=youth_share,
        working_age_share=working_age_share,
        elderly_share=elderly_share,
        urban_pop_pct=urban_pop_pct,
        human_capital=human_capital,
        life_expectancy=life_expectancy,
        gini=gini,
        trade_openness=trade_openness,
        conflict_risk=target_conflict_risk,
        potential_growth=potential_growth,
        structural_unemployment=structural_unemployment,
        urbanization_capacity=urbanization_capacity,
        previous_gdp_growth=potential_growth,
    )

    education_rows = load_range(
        db_conn, code, start_year - HC_PIPELINE_LAG, start_year - 1
    )
    education_by_year = {int(row["year"]): row for row in education_rows}
    historical_education_spend = [
        float(
            education_by_year.get(year, {}).get("education_spend_gdp")
            or DEFAULT_EDUCATION_SPEND_GDP
        )
        for year in range(start_year - HC_PIPELINE_LAG, start_year)
    ]
    state.hc_pipeline = initialize_hc_pipeline(
        state, historical_education_spend
    )
    state.conflict_intercept = calibrate_conflict_intercept(
        state, political_stability
    )
    state.validate_ranges()
    return state
