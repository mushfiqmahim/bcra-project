# Bangladesh Climate Risk Atlas

Free public dashboard tracking satellite-derived climate-risk indicators across all 64 districts of Bangladesh.

**Live app:** https://bcra-project-bd.streamlit.app

## What it does

- **Vegetation health (NDVI)** — 24-month district-level time series derived from Sentinel-2 Surface Reflectance Harmonized imagery.
- **Surface moisture (NDMI)** — 24-month district-level time series derived from Sentinel-2 Surface Reflectance Harmonized imagery.
- **Flood inundation extent** — Area in km² and an interactive folium overlay computed from Sentinel-1 SAR (VV, descending) for the 25 May – 30 June 2024 monsoon window.
- **Coastal salinity proxy** — Two seasonal Bouaziz salinity-index means for the 19 coastal districts, derived from Sentinel-2 Surface Reflectance Harmonized visible bands.

## How it works

Imagery is filtered, masked, and reduced on Google Earth Engine, which performs all heavy raster compute on Google's infrastructure and returns small structured results to the application. Each indicator is reduced over FAO GAUL 2015 admin-level-2 polygons so that outputs are at the district level by construction. The Streamlit application orchestrates the queries, caches them with `@st.cache_data`, and renders Plotly charts, folium maps, and bilingual (English / বাংলা) labels. Deployment is on Streamlit Community Cloud, which rebuilds on every push to `main` and authenticates to Earth Engine via a service account.

## Methodology

The in-app methodology page documents formulas, data sources, interpretation guidance, and limitations for every indicator: https://bcra-project-bd.streamlit.app/methodology

The architectural reference lives at [`docs/project_spec.md`](docs/project_spec.md).

## Local development

Requires Python 3.11+ and a Google account with Earth Engine access.

```bash
git clone https://github.com/mushfiqmahim/bcra-project.git
cd bcra-project
pip install -r requirements.txt
earthengine authenticate
streamlit run app.py
```

## Repository structure

```
app.py                          Streamlit entry point
pages/
  methodology.py                Methodology page
atlas/
  ee_client.py                  Earth Engine init (OAuth local, service account on Cloud)
  ndvi.py                       Sentinel-2 NDVI monthly time series
  moisture.py                   Sentinel-2 NDMI monthly time series
  flood.py                      Sentinel-1 SAR flood extent
  salinity.py                   Sentinel-2 Bouaziz salinity index
  exports.py                    CSV serialization helpers
  i18n.py                       Bilingual string lookup
  ui.py                         Shared sidebar chrome and footer
data/                           District boundaries, coastal-district list, i18n strings
scripts/                        Per-module smoke tests (verify_*.py)
notebooks/                      Indicator sandboxes
docs/project_spec.md            Architectural reference
```

## Tech stack

Python · Streamlit · streamlit-folium · Google Earth Engine (`earthengine-api`) · folium · Plotly · pandas · FAO GAUL 2015 admin-level-2 boundaries.
