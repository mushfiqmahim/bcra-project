"""BCRA dashboard entry point."""
from __future__ import annotations

import logging

import ee
import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from atlas.ee_client import init_ee
from atlas.exports import (
    flood_to_csv,
    ndmi_to_csv,
    ndvi_to_csv,
    salinity_to_csv,
    slugify_district,
)
from atlas.flood import flood_extent
from atlas.i18n import t
from atlas.moisture import ndmi_timeseries
from atlas.ndvi import ndvi_timeseries
from atlas.salinity import is_coastal_district, salinity_seasonal
from atlas.ui import app_footer, sidebar_chrome

st.set_page_config(
    page_title="BCRA — Indicators",
    layout="wide",
)

sidebar_chrome()

init_ee()

_FLOOD_START = "2024-05-25"
_FLOOD_END = "2024-06-30"
_SALINITY_YEAR = 2024


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def _load_district_names() -> list[str]:
    fc = ee.FeatureCollection("FAO/GAUL/2015/level2").filter(
        ee.Filter.eq("ADM0_NAME", "Bangladesh")
    )
    return list(fc.aggregate_array("ADM2_NAME").distinct().sort().getInfo())


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_ndvi(district_name: str, months: int) -> pd.DataFrame:
    return ndvi_timeseries(district_name, months=months)


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_ndmi(
    district_name: str, months: int, end_date: str
) -> pd.DataFrame:
    return ndmi_timeseries(district_name, months, end_date)


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def _cached_salinity(district_name: str, year: int) -> dict:
    return salinity_seasonal(district_name, year)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _cached_flood(district_name: str) -> dict:
    result = flood_extent(district_name, _FLOOD_START, _FLOOD_END)

    tile_url: str | None = None
    map_error_type: str | None = None
    try:
        map_id = result["flood_only_image"].selfMask().getMapId(
            {"min": 0, "max": 1, "palette": ["red"]}
        )
        tile_url = map_id["tile_fetcher"].url_format
    except Exception as exc:
        map_error_type = type(exc).__name__
        logging.exception(
            "Flood map tile generation failed for district %s", district_name
        )

    return {
        "tile_url": tile_url,
        "map_error_type": map_error_type,
        "geojson": result["district_geometry"].getInfo(),
        "flood_only_area_km2": float(result["flood_only_area_km2"]),
        "permanent_water_area_km2": float(result["permanent_water_area_km2"]),
        "flood_total_area_km2": float(result["flood_total_area_km2"]),
    }


st.title(t("app.title"))
st.caption(t("app.caption"))

with st.spinner(t("app.spinner.loading_districts")):
    districts = _load_district_names()

default_idx = districts.index("Khulna") if "Khulna" in districts else 0
district = st.selectbox(t("app.district_selector.label"), districts, index=default_idx)

with st.spinner(t("app.ndvi.spinner").format(district=district)):
    df = _cached_ndvi(district, 24)

latest = df.dropna(subset=["ndvi"]).tail(1)

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["ndvi"],
        mode="lines+markers",
        name="NDVI",
        line=dict(color="#2E7D32", width=2),
        marker=dict(size=6),
        connectgaps=False,
    )
)
if not latest.empty:
    latest_date = latest["date"].iloc[0]
    latest_value = float(latest["ndvi"].iloc[0])
    fig.add_trace(
        go.Scatter(
            x=[latest_date],
            y=[latest_value],
            mode="markers+text",
            marker=dict(color="#D84315", size=12),
            text=[f"{latest_value:.3f}"],
            textposition="top center",
            showlegend=False,
        )
    )

fig.update_layout(
    title=t("app.ndvi.chart_title").format(district=district),
    xaxis_title=t("app.ndvi.xaxis_title"),
    yaxis_title=t("app.ndvi.yaxis_title"),
    yaxis=dict(range=[0, 1]),
    template="simple_white",
    height=440,
    margin=dict(l=60, r=30, t=60, b=50),
)
st.plotly_chart(fig, use_container_width=True)

st.download_button(
    t("app.download_button"),
    data=ndvi_to_csv(df, district),
    file_name=(
        f"bcra_ndvi_{slugify_district(district)}_24m_"
        f"{pd.Timestamp.today().normalize():%Y-%m-%d}.csv"
    ),
    mime="text/csv",
    key="download_ndvi_csv",
)

st.divider()

ndmi_end_date = pd.Timestamp.today().normalize().strftime("%Y-%m-%d")
with st.spinner(t("app.ndmi.spinner").format(district=district)):
    ndmi_df = _cached_ndmi(district, 24, ndmi_end_date)

ndmi_latest = ndmi_df.dropna(subset=["ndmi"]).tail(1)

ndmi_fig = go.Figure()
ndmi_fig.add_trace(
    go.Scatter(
        x=ndmi_df["date"],
        y=ndmi_df["ndmi"],
        mode="lines+markers",
        name="NDMI",
        line=dict(color="#0277BD", width=2),
        marker=dict(size=6),
        connectgaps=False,
    )
)
if not ndmi_latest.empty:
    ndmi_latest_date = ndmi_latest["date"].iloc[0]
    ndmi_latest_value = float(ndmi_latest["ndmi"].iloc[0])
    ndmi_fig.add_trace(
        go.Scatter(
            x=[ndmi_latest_date],
            y=[ndmi_latest_value],
            mode="markers+text",
            marker=dict(color="#D84315", size=12),
            text=[f"{ndmi_latest_value:.3f}"],
            textposition="top center",
            showlegend=False,
        )
    )

ndmi_fig.update_layout(
    title=t("app.ndmi.chart_title").format(district=district),
    xaxis_title=t("app.ndmi.xaxis_title"),
    yaxis_title=t("app.ndmi.yaxis_title"),
    yaxis=dict(range=[-0.5, 0.7]),
    template="simple_white",
    height=440,
    margin=dict(l=60, r=30, t=60, b=50),
)
st.plotly_chart(ndmi_fig, use_container_width=True)

st.download_button(
    t("app.download_button"),
    data=ndmi_to_csv(ndmi_df, district),
    file_name=f"bcra_ndmi_{slugify_district(district)}_24m_{ndmi_end_date}.csv",
    mime="text/csv",
    key="download_ndmi_csv",
)

st.divider()

st.subheader(t("app.flood.heading"))

with st.spinner(t("app.flood.spinner").format(district=district)):
    flood = _cached_flood(district)

flood_cols = st.columns(3)
flood_cols[0].metric(
    t("app.flood.metric.flood_only"), f"{flood['flood_only_area_km2']:.1f}"
)
flood_cols[1].metric(
    t("app.flood.metric.permanent_water"), f"{flood['permanent_water_area_km2']:.1f}"
)
flood_cols[2].metric(
    t("app.flood.metric.flood_total"), f"{flood['flood_total_area_km2']:.1f}"
)

if flood["tile_url"] is not None:
    district_layer = folium.GeoJson(
        flood["geojson"],
        name=t("app.flood.layer.district_boundary"),
        style_function=lambda feature: {
            "color": "black",
            "weight": 2,
            "fillOpacity": 0,
        },
    )
    bounds = district_layer.get_bounds()
    center = [
        (bounds[0][0] + bounds[1][0]) / 2,
        (bounds[0][1] + bounds[1][1]) / 2,
    ]

    fmap = folium.Map(location=center, zoom_start=9, tiles="OpenStreetMap")
    folium.raster_layers.TileLayer(
        tiles=flood["tile_url"],
        attr="Google Earth Engine",
        name=t("app.flood.layer.flood_extent"),
        overlay=True,
        control=True,
        opacity=0.6,
    ).add_to(fmap)
    district_layer.add_to(fmap)
    fmap.fit_bounds(bounds)
    folium.LayerControl().add_to(fmap)

    st_folium(fmap, height=480, use_container_width=True, returned_objects=[])
else:
    st.info(t("app.flood.map_unavailable"))

st.download_button(
    t("app.download_button"),
    data=flood_to_csv(
        {
            "flood_only_area_km2": flood["flood_only_area_km2"],
            "permanent_water_area_km2": flood["permanent_water_area_km2"],
            "flood_total_area_km2": flood["flood_total_area_km2"],
        },
        district,
        _FLOOD_START,
        _FLOOD_END,
    ),
    file_name=(
        f"bcra_flood_{slugify_district(district)}_"
        f"{_FLOOD_START}_to_{_FLOOD_END}.csv"
    ),
    mime="text/csv",
    key="download_flood_csv",
)

st.divider()

st.subheader(t("app.salinity.heading").format(year=_SALINITY_YEAR))

if is_coastal_district(district):
    with st.spinner(t("app.salinity.spinner").format(district=district)):
        salinity = _cached_salinity(district, _SALINITY_YEAR)

    salinity_cols = st.columns(2)
    dry = salinity["dry_season_si"]
    monsoon = salinity["monsoon_season_si"]
    salinity_cols[0].metric(
        t("app.salinity.metric.dry_season"),
        f"{dry:.3f}" if dry is not None else t("app.salinity.metric.na"),
    )
    salinity_cols[1].metric(
        t("app.salinity.metric.monsoon_season"),
        f"{monsoon:.3f}" if monsoon is not None else t("app.salinity.metric.na"),
    )
    st.download_button(
        t("app.download_button"),
        data=salinity_to_csv(salinity, district),
        file_name=(
            f"bcra_salinity_{slugify_district(district)}_{_SALINITY_YEAR}.csv"
        ),
        mime="text/csv",
        key="download_salinity_csv",
    )
else:
    st.caption(
        t("app.salinity.inland_caption").format(district=district)
    )

app_footer()

