import math
import sqlite3

import pytest

from engine.core.helpers import clamp, finite_float, trimmed_mean
from engine.data.country_loader import (
    DEFAULT_DB_PATH,
    connection_scope,
    load_country_metadata,
    load_nearest_value,
    load_range,
    load_year,
)


def test_helper_error_contracts_and_short_trimmed_series():
    with pytest.raises(ValueError, match="Invalid clamp bounds"):
        clamp(1.0, 2.0, 0.0)
    with pytest.raises(ValueError, match="at least one"):
        trimmed_mean([])
    with pytest.raises(ValueError, match="trim must be"):
        trimmed_mean([1.0, 2.0], trim=0.5)
    assert trimmed_mean([1.0, 3.0], trim=0.1) == pytest.approx(2.0)
    with pytest.raises(ValueError, match="must be numeric"):
        finite_float(object(), "value")
    with pytest.raises(ValueError, match="must be finite"):
        finite_float(math.inf, "value")


def test_connection_scope_preserves_caller_connection_factory():
    connection = sqlite3.connect(DEFAULT_DB_PATH)
    original = connection.row_factory
    try:
        with connection_scope(connection) as scoped:
            assert scoped is connection
            assert scoped.row_factory is sqlite3.Row
        assert connection.row_factory is original
    finally:
        connection.close()


def test_connection_scope_rejects_missing_database(tmp_path):
    with pytest.raises(FileNotFoundError, match="database not found"):
        with connection_scope(tmp_path / "missing.db"):
            pass


def test_loader_metadata_range_and_error_paths():
    metadata = load_country_metadata(DEFAULT_DB_PATH, "ken")
    assert metadata["iso3"] == "KEN"
    assert metadata["country_name"]

    with pytest.raises(LookupError, match="Unknown country code"):
        load_country_metadata(DEFAULT_DB_PATH, "ZZZ")
    with pytest.raises(LookupError, match="Unknown country code"):
        load_year(DEFAULT_DB_PATH, "ZZZ", 2023)
    with pytest.raises(LookupError, match="Unknown country code"):
        load_range(DEFAULT_DB_PATH, "ZZZ", 2020, 2023)

    assert load_range(DEFAULT_DB_PATH, "KEN", 2023, 2022) == []
    rows = load_range(DEFAULT_DB_PATH, "KEN", 2022, 2023)
    assert [row["year"] for row in rows] == [2022, 2023]
    assert all("gdp_current_usd" in row for row in rows)

    with pytest.raises(ValueError, match="Unsupported warehouse field"):
        load_nearest_value(DEFAULT_DB_PATH, "KEN", "countries", "iso3", 2023)
