"""Shared, authenticated-free download helpers for public statistical sources."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_ROOT = Path(
    os.environ.get("POLITY_RAW_DATA", PROJECT_ROOT / "data" / "raw")
).expanduser().resolve()
USER_AGENT = "POLITY-Engine/1.0 research-data-fetcher"


def download_file(
    url: str,
    relative_target: str,
    *,
    params: Mapping[str, object] | None = None,
    timeout: int = 120,
) -> Path:
    """Download one public file atomically and return its absolute path."""

    target = RAW_DATA_ROOT / relative_target
    target.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        url,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(response.content)
    temporary.replace(target)
    print(f"Saved: {target}")
    return target


def download_world_bank_indicator(indicator: str, relative_target: str) -> Path:
    url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator}"
    return download_file(
        url,
        relative_target,
        params={"format": "json", "per_page": 20000},
    )
