"""Historical data access for POLITY initialization."""

from engine.data.country_loader import (
    DB_PATH,
    DEFAULT_DB_PATH,
    load_country,
    load_country_metadata,
    load_nearest_value,
    load_range,
    load_year,
)

__all__ = [
    "DB_PATH",
    "DEFAULT_DB_PATH",
    "load_country",
    "load_country_metadata",
    "load_nearest_value",
    "load_range",
    "load_year",
]
