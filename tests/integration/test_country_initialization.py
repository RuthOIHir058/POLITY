from pathlib import Path

import pytest

from engine.core.initialize_country import initialize_country
from engine.data.country_loader import DEFAULT_DB_PATH, load_country, load_range, load_year
from engine.politics.stability import evaluate_conflict_risk


def test_raw_loader_preserves_warehouse_units():
    row = load_year(DEFAULT_DB_PATH, "KEN", 2023)
    assert row["gdp_current_usd"] == pytest.approx(107_500_884_685.013)
    assert row["inflation"] == pytest.approx(7.67139634029402)
    assert row["debt_gdp"] == pytest.approx(73.4)


def test_initializer_converts_to_canonical_ratios_and_calibrates():
    state = initialize_country("KEN", 2023, DEFAULT_DB_PATH)
    assert state.country_code == "KEN"
    assert state.inflation == pytest.approx(0.0767139634029402)
    assert state.debt_gdp == pytest.approx(0.734)
    assert state.trade_openness == pytest.approx(0.411110904167395)
    assert state.gini == pytest.approx(0.40)
    assert state.fiscal_capacity == pytest.approx(
        (16.989570500735 / 100.0) / 0.40
    )
    assert len(state.hc_pipeline) == 15

    risk = evaluate_conflict_risk(
        state,
        state.unemployment,
        state.previous_gdp_growth,
        state.gini,
        state.inflation,
        0.0,
    ).conflict_risk
    assert risk == pytest.approx(state.conflict_risk)


def test_loader_uses_project_relative_default_from_any_working_directory(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    state = load_country("KEN", 2023)
    assert state.country_code == "KEN"
    assert state.gdp > 0.0


def test_load_range_is_ordered_and_merged():
    rows = load_range(DEFAULT_DB_PATH, "KEN", 2019, 2023)
    assert [row["year"] for row in rows] == [2019, 2020, 2021, 2022, 2023]
    assert all(row["country_code"] == "KEN" for row in rows)
