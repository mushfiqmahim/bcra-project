"""Sentinel-2 NDVI monthly time series for Bangladesh districts."""
from __future__ import annotations

import ee
import pandas as pd

_S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
_GAUL_LEVEL2 = "FAO/GAUL/2015/level2"
_CLOUD_PCT_MAX = 60
_REDUCE_SCALE = 100
_MAX_PIXELS = int(1e9)


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


def _add_ndvi(image: ee.Image) -> ee.Image:
    return image.addBands(
        image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    )


def ndvi_timeseries(
    district_name: str,
    months: int = 24,
    end_date: ee.Date | None = None,
) -> pd.DataFrame:
    """Compute monthly mean NDVI for a Bangladesh district.

    Builds a single Sentinel-2 image with one NDVI band per month over the
    requested window and reduces it to district-mean values in one server
    call. Months with no usable scenes return NaN.

    Args:
        district_name: ADM2_NAME from FAO/GAUL/2015/level2 (e.g., "Khulna").
        months: Number of monthly windows to compute, ending at end_date.
        end_date: Right edge of the window. Defaults to today.

    Returns:
        DataFrame with columns 'date' (datetime64, first-of-month) and
        'ndvi' (float, NaN for empty months), sorted by date ascending.
    """
    if end_date is None:
        end_py = pd.Timestamp.today().normalize()
        end_ee = ee.Date(end_py.strftime("%Y-%m-%d"))
    else:
        end_ee = end_date
        end_py = pd.Timestamp(end_ee.format("YYYY-MM-dd").getInfo())

    districts = ee.FeatureCollection(_GAUL_LEVEL2).filter(
        ee.Filter.eq("ADM0_NAME", "Bangladesh")
    )
    geom = (
        districts.filter(ee.Filter.eq("ADM2_NAME", district_name))
        .first()
        .geometry()
    )

    start_ee = end_ee.advance(-(months - 1), "month")
    window_end_ee = end_ee.advance(1, "month")

    collection = (
        ee.ImageCollection(_S2_COLLECTION)
        .filterBounds(geom)
        .filterDate(start_ee, window_end_ee)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", _CLOUD_PCT_MAX))
        .map(_mask_s2_clouds)
        .map(_add_ndvi)
    )

    masked_constant = ee.Image.constant(0).updateMask(ee.Image.constant(0))

    bands: list[ee.Image] = []
    band_names: list[str] = []
    dates: list[pd.Timestamp] = []

    for i in range(months):
        offset = -(months - 1) + i
        m_start_ee = end_ee.advance(offset, "month")
        m_end_ee = m_start_ee.advance(1, "month")
        m_start_py = end_py + pd.DateOffset(months=offset)

        band_name = f"ndvi_{m_start_py.year:04d}_{m_start_py.month:02d}"
        band_names.append(band_name)
        dates.append(
            pd.Timestamp(year=m_start_py.year, month=m_start_py.month, day=1)
        )

        monthly = collection.filterDate(m_start_ee, m_end_ee).select("NDVI")
        band = ee.Image(
            ee.Algorithms.If(
                monthly.size().gt(0),
                monthly.mean().rename(band_name),
                masked_constant.rename(band_name),
            )
        )
        bands.append(band)

    stacked = ee.Image.cat(bands)

    stats = stacked.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=_REDUCE_SCALE,
        maxPixels=_MAX_PIXELS,
    ).getInfo()

    rows = [
        (
            date,
            float(stats[name]) if stats.get(name) is not None else float("nan"),
        )
        for name, date in zip(band_names, dates)
    ]
    df = pd.DataFrame(rows, columns=["date", "ndvi"])
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)
