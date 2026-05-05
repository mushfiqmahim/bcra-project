"""Sentinel-1 SAR flood extent for Bangladesh districts."""
from __future__ import annotations

import ee

_S1_COLLECTION = "COPERNICUS/S1_GRD"
_GAUL_LEVEL2 = "FAO/GAUL/2015/level2"
_JRC_GSW = "JRC/GSW1_4/GlobalSurfaceWater"
_PERMANENT_OCCURRENCE_PCT = 50
_REDUCE_SCALE = 30
_MAX_PIXELS = int(1e9)
_PRE_LEAD_DAYS = 25
_PRE_LAG_DAYS = 5


def _district_geometry(district_name: str) -> ee.Geometry:
    return (
        ee.FeatureCollection(_GAUL_LEVEL2)
        .filter(ee.Filter.eq("ADM0_NAME", "Bangladesh"))
        .filter(ee.Filter.eq("ADM2_NAME", district_name))
        .first()
        .geometry()
    )


def _vv_collection(
    geom: ee.Geometry,
    start: ee.Date,
    end: ee.Date,
    orbit_pass: str,
) -> ee.ImageCollection:
    return (
        ee.ImageCollection(_S1_COLLECTION)
        .filterBounds(geom)
        .filterDate(start, end)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.eq("orbitProperties_pass", orbit_pass))
        .select("VV")
    )


def _water_area_km2(mask: ee.Image, geom: ee.Geometry) -> float:
    area = mask.multiply(ee.Image.pixelArea()).divide(1e6).rename("area")
    value = area.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geom,
        scale=_REDUCE_SCALE,
        maxPixels=_MAX_PIXELS,
    ).get("area").getInfo()
    return float(value) if value is not None else 0.0


def flood_extent(
    district_name: str,
    flood_start: str,
    flood_end: str,
    pre_start: str | None = None,
    pre_end: str | None = None,
    orbit_pass: str = "DESCENDING",
    threshold_db: float = -16,
) -> dict:
    """Detect Sentinel-1 SAR flood extent for a Bangladesh district.

    Median-composites VV backscatter over the flood window, thresholds at
    `threshold_db` dB, and removes JRC GSW permanent water via updateMask.
    Returns the flood-only mask plus area accounting in square kilometers.

    Args:
        district_name: ADM2_NAME from FAO/GAUL/2015/level2.
        flood_start: ISO date 'YYYY-MM-DD' for the flood window start.
        flood_end: ISO date 'YYYY-MM-DD' for the flood window end (exclusive).
        pre_start: Pre-flood baseline start. Defaults to flood_start - 25 days.
        pre_end: Pre-flood baseline end. Defaults to flood_start - 5 days.
        orbit_pass: 'DESCENDING' or 'ASCENDING'.
        threshold_db: VV backscatter threshold below which pixels are water.

    Returns:
        Dict with 'flood_only_image', 'flood_only_area_km2',
        'permanent_water_area_km2', 'flood_total_area_km2', 'district_geometry'.
    """
    flood_start_ee = ee.Date(flood_start)
    flood_end_ee = ee.Date(flood_end)
    pre_start_ee = (
        ee.Date(pre_start)
        if pre_start is not None
        else flood_start_ee.advance(-_PRE_LEAD_DAYS, "day")
    )
    pre_end_ee = (
        ee.Date(pre_end)
        if pre_end is not None
        else flood_start_ee.advance(-_PRE_LAG_DAYS, "day")
    )

    geom = _district_geometry(district_name)

    pre_collection = _vv_collection(geom, pre_start_ee, pre_end_ee, orbit_pass)
    flood_collection = _vv_collection(
        geom, flood_start_ee, flood_end_ee, orbit_pass
    )

    masked_constant = ee.Image.constant(0).updateMask(ee.Image.constant(0))
    pre_composite = ee.Image(
        ee.Algorithms.If(
            pre_collection.size().gt(0),
            pre_collection.median().clip(geom),
            masked_constant,
        )
    )
    flood_composite = flood_collection.median().clip(geom)

    permanent_water = (
        ee.Image(_JRC_GSW)
        .select("occurrence")
        .gt(_PERMANENT_OCCURRENCE_PCT)
        .unmask(0)
        .rename("water")
    )

    flood_water = flood_composite.lt(threshold_db).rename("water")
    flood_only = flood_water.updateMask(permanent_water.eq(0)).rename("water")

    return {
        "flood_only_image": flood_only,
        "flood_only_area_km2": _water_area_km2(flood_only, geom),
        "permanent_water_area_km2": _water_area_km2(
            permanent_water.clip(geom), geom
        ),
        "flood_total_area_km2": _water_area_km2(flood_water, geom),
        "district_geometry": geom,
    }
