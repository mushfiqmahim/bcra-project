"""Smoke test for atlas.exports CSV helpers (no Earth Engine)."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from atlas.exports import (
    flood_to_csv,
    ndmi_to_csv,
    ndvi_to_csv,
    salinity_to_csv,
    slugify_district,
)


def main() -> None:
    assert slugify_district("Cox's Bazar") == "coxs_bazar"
    assert slugify_district("Khulna") == "khulna"
    assert slugify_district("Bagerhat") == "bagerhat"
    print("slugify_district: OK")

    ndvi_df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
            "ndvi": [0.5, float("nan"), 0.7],
        }
    )
    ndvi_csv = ndvi_to_csv(ndvi_df, "Khulna")
    assert ndvi_csv, "ndvi_to_csv should return a non-empty string"
    assert ndvi_csv.endswith("\n"), "NDVI CSV should end with a newline"
    assert ndvi_csv.split("\n")[0] == "date,ndvi,district", (
        f"unexpected NDVI header: {ndvi_csv.split(chr(10))[0]!r}"
    )
    parsed_ndvi = pd.read_csv(io.StringIO(ndvi_csv))
    assert len(parsed_ndvi) == 3, f"expected 3 rows, got {len(parsed_ndvi)}"
    assert list(parsed_ndvi.columns) == ["date", "ndvi", "district"]
    assert pd.isna(parsed_ndvi.iloc[1]["ndvi"]), "NaN should roundtrip as NaN"
    print("ndvi_to_csv: OK (3 rows, header date,ndvi,district, NaN roundtrip)")

    ndmi_df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01"]),
            "ndmi": [0.2, 0.3],
        }
    )
    ndmi_csv = ndmi_to_csv(ndmi_df, "Rangpur")
    assert ndmi_csv, "ndmi_to_csv should return a non-empty string"
    assert ndmi_csv.endswith("\n"), "NDMI CSV should end with a newline"
    assert ndmi_csv.split("\n")[0] == "date,ndmi,district", (
        f"unexpected NDMI header: {ndmi_csv.split(chr(10))[0]!r}"
    )
    print("ndmi_to_csv: OK (header date,ndmi,district)")

    salinity_csv = salinity_to_csv(
        {
            "dry_season_si": 0.084,
            "monsoon_season_si": 0.104,
            "district_name": "Khulna",
            "year": 2024,
        },
        "Khulna",
    )
    assert salinity_csv, "salinity_to_csv should return a non-empty string"
    assert salinity_csv.endswith("\n"), "salinity CSV should end with a newline"
    parsed_salinity = pd.read_csv(io.StringIO(salinity_csv))
    assert len(parsed_salinity) == 1, "salinity CSV should have 1 row"
    assert len(parsed_salinity.columns) == 4, (
        f"expected 4 columns, got {len(parsed_salinity.columns)}"
    )
    print("salinity_to_csv: OK (1 row, 4 columns)")

    salinity_none_csv = salinity_to_csv(
        {
            "dry_season_si": 0.084,
            "monsoon_season_si": None,
            "district_name": "Khulna",
            "year": 2024,
        },
        "Khulna",
    )
    parsed_none = pd.read_csv(io.StringIO(salinity_none_csv))
    assert pd.isna(parsed_none.iloc[0]["monsoon_season_si"]), (
        "None should serialize to an empty cell that parses back as NaN"
    )
    print("salinity_to_csv None: OK (None -> empty cell -> NaN)")

    flood_csv = flood_to_csv(
        {
            "flood_only_area_km2": 1301.5,
            "permanent_water_area_km2": 102.9,
            "flood_total_area_km2": 1448.6,
        },
        "Sylhet",
        "2024-05-25",
        "2024-06-30",
    )
    assert flood_csv, "flood_to_csv should return a non-empty string"
    assert flood_csv.endswith("\n"), "flood CSV should end with a newline"
    parsed_flood = pd.read_csv(io.StringIO(flood_csv))
    assert len(parsed_flood) == 1, "flood CSV should have 1 row"
    assert len(parsed_flood.columns) == 6, (
        f"expected 6 columns, got {len(parsed_flood.columns)}"
    )
    print("flood_to_csv: OK (1 row, 6 columns)")

    print("\nAll export checks passed.")


if __name__ == "__main__":
    main()
