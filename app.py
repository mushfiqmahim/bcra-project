"""BCRA dashboard entry point."""
from __future__ import annotations

import ee
import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from atlas.ee_client import init_ee
from atlas.flood import flood_extent
from atlas.moisture import ndmi_timeseries
from atlas.ndvi import ndvi_timeseries

st.set_page_config(
    page_title="BCRA — Bangladesh Climate Risk Atlas",
    layout="wide",
)

init_ee()

_FLOOD_START = "2024-05-25"
_FLOOD_END = "2024-06-30"


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


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _cached_flood(district_name: str) -> dict:
    result = flood_extent(district_name, _FLOOD_START, _FLOOD_END)
    map_id = result["flood_only_image"].selfMask().getMapId(
        {"min": 0, "max": 1, "palette": ["red"]}
    )
    return {
        "tile_url": map_id["tile_fetcher"].url_format,
        "geojson": result["district_geometry"].getInfo(),
        "flood_only_area_km2": float(result["flood_only_area_km2"]),
        "permanent_water_area_km2": float(result["permanent_water_area_km2"]),
        "flood_total_area_km2": float(result["flood_total_area_km2"]),
    }


st.title("Bangladesh Climate Risk Atlas")
st.caption("Sentinel-2 NDVI monthly time series at the district level.")

with st.spinner("Loading districts…"):
    districts = _load_district_names()

default_idx = districts.index("Khulna") if "Khulna" in districts else 0
district = st.selectbox("District", districts, index=default_idx)

with st.spinner(f"Computing NDVI for {district}…"):
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
    title=f"{district} — Monthly Mean NDVI (Sentinel-2, 24 months)",
    xaxis_title="Month",
    yaxis_title="NDVI",
    yaxis=dict(range=[0, 1]),
    template="simple_white",
    height=440,
    margin=dict(l=60, r=30, t=60, b=50),
)
st.plotly_chart(fig, use_container_width=True)

ndmi_end_date = pd.Timestamp.today().normalize().strftime("%Y-%m-%d")
with st.spinner(f"Computing NDMI for {district}…"):
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
    title=f"{district} — Monthly Mean NDMI (Sentinel-2, 24 months)",
    xaxis_title="Month",
    yaxis_title="NDMI",
    yaxis=dict(range=[-0.5, 0.7]),
    template="simple_white",
    height=440,
    margin=dict(l=60, r=30, t=60, b=50),
)
st.plotly_chart(ndmi_fig, use_container_width=True)

st.subheader("Flood extent — 2024 monsoon (May 25 – Jun 30)")

with st.spinner(f"Computing flood extent for {district}…"):
    flood = _cached_flood(district)

flood_cols = st.columns(3)
flood_cols[0].metric(
    "Flood-only extent (km²)", f"{flood['flood_only_area_km2']:.1f}"
)
flood_cols[1].metric(
    "Permanent water (km²)", f"{flood['permanent_water_area_km2']:.1f}"
)
flood_cols[2].metric(
    "Flood total (km²)", f"{flood['flood_total_area_km2']:.1f}"
)

district_layer = folium.GeoJson(
    flood["geojson"],
    name="District boundary",
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
    name="Flood extent (May 25 – Jun 30, 2024)",
    overlay=True,
    control=True,
    opacity=0.6,
).add_to(fmap)
district_layer.add_to(fmap)
fmap.fit_bounds(bounds)
folium.LayerControl().add_to(fmap)

st_folium(fmap, height=480, use_container_width=True, returned_objects=[])
