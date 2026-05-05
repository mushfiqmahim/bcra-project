"""BCRA dashboard entry point."""
from __future__ import annotations

import ee
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from atlas.ee_client import init_ee
from atlas.ndvi import ndvi_timeseries

st.set_page_config(
    page_title="BCRA — Bangladesh Climate Risk Atlas",
    layout="wide",
)

init_ee()


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def _load_district_names() -> list[str]:
    fc = ee.FeatureCollection("FAO/GAUL/2015/level2").filter(
        ee.Filter.eq("ADM0_NAME", "Bangladesh")
    )
    return list(fc.aggregate_array("ADM2_NAME").distinct().sort().getInfo())


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_ndvi(district_name: str, months: int) -> pd.DataFrame:
    return ndvi_timeseries(district_name, months=months)


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
