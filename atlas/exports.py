"""CSV export helpers for BCRA indicator dataframes and result dicts."""
from __future__ import annotations

import io
import re

import pandas as pd

_DATE_FORMAT = "%Y-%m-%d"


def slugify_district(name: str) -> str:
    return re.sub(r"\s+", "_", name.replace("'", "").lower())


def ndvi_to_csv(df: pd.DataFrame, district_name: str) -> str:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime(_DATE_FORMAT)
    out["district"] = district_name
    buffer = io.StringIO()
    out[["date", "ndvi", "district"]].to_csv(buffer, index=False, lineterminator="\n")
    return buffer.getvalue()


def ndmi_to_csv(df: pd.DataFrame, district_name: str) -> str:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime(_DATE_FORMAT)
    out["district"] = district_name
    buffer = io.StringIO()
    out[["date", "ndmi", "district"]].to_csv(buffer, index=False, lineterminator="\n")
    return buffer.getvalue()


def salinity_to_csv(result: dict, district_name: str) -> str:
    row = pd.DataFrame(
        [
            {
                "district": district_name,
                "year": result["year"],
                "dry_season_si": result["dry_season_si"],
                "monsoon_season_si": result["monsoon_season_si"],
            }
        ]
    )
    buffer = io.StringIO()
    row.to_csv(buffer, index=False, lineterminator="\n")
    return buffer.getvalue()


def flood_to_csv(
    result: dict,
    district_name: str,
    flood_start: str,
    flood_end: str,
) -> str:
    row = pd.DataFrame(
        [
            {
                "district": district_name,
                "flood_start": flood_start,
                "flood_end": flood_end,
                "flood_only_area_km2": result["flood_only_area_km2"],
                "permanent_water_area_km2": result["permanent_water_area_km2"],
                "flood_total_area_km2": result["flood_total_area_km2"],
            }
        ]
    )
    buffer = io.StringIO()
    row.to_csv(buffer, index=False, lineterminator="\n")
    return buffer.getvalue()
