"""Sentinel-2 Bouaziz salinity index seasonal means for coastal Bangladesh."""
from __future__ import annotations

import json
from pathlib import Path

import ee

_S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
_GAUL_LEVEL2 = "FAO/GAUL/2015/level2"
_CLOUD_PCT_MAX = 60
_REDUCE_SCALE = 100
_MAX_PIXELS = int(1e9)
_DRY_START_MONTH = 3
_DRY_END_MONTH = 6
_MONSOON_START_MONTH = 7
_MONSOON_END_MONTH = 10

_COASTAL_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "coastal_districts.json"
)


def _load_coastal_districts() -> tuple[str, ...]:
    with _COASTAL_PATH.open(encoding="utf-8") as f:
        return tuple(json.load(f))


COASTAL_DISTRICTS: tuple[str, ...] = _load_coastal_districts()


def _mask_s2_clouds(image: ee.Image) -> ee.Image:
    qa = image.select("QA60")
    cloud_bit = 1 << 10
    cirrus_bit = 1 << 11
    mask = (
        qa.bitwiseAnd(cloud_bit).eq(0)
        .And(qa.bitwiseAnd(cirrus_bit).eq(0))
    )
    return (
        image.updateMask(mask)
        .divide(10000)
        .copyProperties(image, ["system:time_start"])
    )


def _add_salinity_index(image: ee.Image) -> ee.Image:
    si = image.select("B2").multiply(image.select("B4")).sqrt().rename("SI")
    return image.addBands(si)


def _district_geometry(district_name: str) -> ee.Geometry:
    return (
        ee.FeatureCollection(_GAUL_LEVEL2)
        .filter(ee.Filter.eq("ADM0_NAME", "Bangladesh"))
        .filter(ee.Filter.eq("ADM2_NAME", district_name))
        .first()
        .geometry()
    )


def _season_band(
    collection: ee.ImageCollection,
    start: ee.Date,
    end: ee.Date,
    band_name: str,
    masked_constant: ee.Image,
) -> ee.Image:
    season = collection.filterDate(start, end).select("SI")
    return ee.Image(
        ee.Algorithms.If(
            season.size().gt(0),
            season.mean().rename(band_name),
            masked_constant.rename(band_name),
        )
    )


def is_coastal_district(district_name: str) -> bool:
    return district_name in COASTAL_DISTRICTS


def salinity_seasonal(
    district_name: str,
    year: int,
) -> dict:
    """Compute dry-season and monsoon-season Bouaziz salinity index means.

    SI = sqrt(B2 * B4) on Sentinel-2 SR Harmonized at physical reflectance,
    averaged across all cloud-masked scenes in each season window and
    reduced to the district mean. Both seasonal bands are stacked and
    reduced in a single Earth Engine round-trip.

    Args:
        district_name: ADM2_NAME from FAO/GAUL/2015/level2; must be coastal.
        year: Calendar year for both seasonal windows.

    Returns:
        Dict with 'dry_season_si' and 'monsoon_season_si' (float or None
        when a season has no usable scenes), 'district_name', and 'year'.

    Raises:
        ValueError: if district_name is not in COASTAL_DISTRICTS.
    """
    if not is_coastal_district(district_name):
        raise ValueError(
            f"{district_name!r} is not a coastal district. "
            f"Gate callers with atlas.salinity.is_coastal_district()."
        )

    geom = _district_geometry(district_name)

    dry_start = ee.Date.fromYMD(year, _DRY_START_MONTH, 1)
    dry_end = ee.Date.fromYMD(year, _DRY_END_MONTH, 1)
    monsoon_start = ee.Date.fromYMD(year, _MONSOON_START_MONTH, 1)
    monsoon_end = ee.Date.fromYMD(year, _MONSOON_END_MONTH, 1)

    collection = (
        ee.ImageCollection(_S2_COLLECTION)
        .filterBounds(geom)
        .filterDate(dry_start, monsoon_end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", _CLOUD_PCT_MAX))
        .map(_mask_s2_clouds)
        .map(_add_salinity_index)
    )

    masked_constant = ee.Image.constant(0).updateMask(ee.Image.constant(0))

    dry_band = _season_band(
        collection, dry_start, dry_end, "dry", masked_constant
    )
    monsoon_band = _season_band(
        collection, monsoon_start, monsoon_end, "monsoon", masked_constant
    )

    stacked = ee.Image.cat([dry_band, monsoon_band])

    stats = stacked.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=_REDUCE_SCALE,
        maxPixels=_MAX_PIXELS,
    ).getInfo()

    return {
        "dry_season_si": (
            float(stats["dry"]) if stats.get("dry") is not None else None
        ),
        "monsoon_season_si": (
            float(stats["monsoon"])
            if stats.get("monsoon") is not None
            else None
        ),
        "district_name": district_name,
        "year": year,
    }
