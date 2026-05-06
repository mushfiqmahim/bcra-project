# Bangladesh Climate Risk Atlas

A free, public web dashboard tracking climate-risk indicators for every
district of Bangladesh. Computed on Google Earth Engine; bilingual English /
বাংলা.

- **Live application:** https://bcra-project-bd.streamlit.app
- **Methodology and limitations:** https://bcra-project-bd.streamlit.app/methodology

## Indicators

| Indicator | Source | Output |
|-----------|--------|--------|
| Vegetation health (NDVI) | Sentinel-2 SR Harmonized, B8 / B4 normalized difference | 24-month time series |
| Surface moisture (NDMI) | Sentinel-2 SR Harmonized, B8 / B11 normalized difference | 24-month time series |
| Flood inundation extent | Sentinel-1 SAR (VV, descending) | Area (km²) and folium map for the 25 May – 30 Jun 2024 window |
| Coastal salinity (proxy) | Sentinel-2 SR Harmonized, Bouaziz SI = √(B2 × B4) | Two seasonal means, restricted to 19 coastal districts |

The salinity indicator is a visible-band brightness proxy, not a calibrated
soil-salinity measurement. See the methodology page for full limitations.

## Validation

| Indicator | Test | Expected | Observed |
|-----------|------|----------|----------|
| Flood (Sylhet, 2024 monsoon) | flood-only extent | > 1000 km² | **1,301.5 km²** (37.4 % of district) |
| Flood (Sylhet, dry-season control) | flood-only extent | < 100 km² | **27.9 km²** (0.8 % of district) |
| NDVI (Rangpur, 12 months) | non-null monthly composites | ≥ 9 of 12 | yes |
| NDMI (Khulna, 12 months) | values within [−0.5, 0.7] | yes | yes |
| Salinity (all 19 coastal districts) | values within [0, 0.3] | yes | yes |

Per-module smoke tests live in `scripts/verify_*.py`. Each runs standalone:

```bash
python scripts/verify_ndvi.py
python scripts/verify_ndmi.py
python scripts/verify_flood.py
python scripts/verify_salinity.py
python scripts/verify_exports.py
python scripts/verify_i18n.py
```

## Run locally

Requires Python 3.11+ and a Google account with Earth Engine access.

```bash
git clone https://github.com/mushfiqmahim/bcra-project.git
cd bcra-project
pip install -r requirements.txt
earthengine authenticate          # one-time OAuth flow
streamlit run app.py
```

Earth Engine project: `earth-engine-project-495404` (Community Tier, free for
non-commercial use).

## Architecture

```
app.py                          Streamlit entry point
pages/methodology.py            Methodology page
atlas/ee_client.py              Earth Engine init (OAuth local, service account on Cloud)
atlas/ndvi.py                   Sentinel-2 NDVI monthly time series
atlas/moisture.py               Sentinel-2 NDMI monthly time series
atlas/flood.py                  Sentinel-1 SAR flood extent
atlas/salinity.py               Sentinel-2 Bouaziz salinity index
atlas/exports.py                CSV serialization helpers
atlas/i18n.py                   Bilingual string lookup
atlas/ui.py                     Shared sidebar chrome and footer
data/strings.json               99 i18n keys (English + Bangla)
data/coastal_districts.json     19 ADM2 names matching FAO GAUL spellings
scripts/verify_*.py             Per-module smoke tests
docs/project_spec.md            Architectural reference
docs/session_handoff.md         Operational state and friction log
```

## Tech stack

Python 3.11 (local) / 3.14 (Streamlit Cloud). Streamlit + streamlit-folium for
UI. `earthengine-api` for Earth Engine access. folium, plotly, pandas for
rendering and shaping. FAO GAUL 2015 admin level 2 for district boundaries.

## License

MIT — see [`LICENSE`](LICENSE).

## Maintainer

Mushfiq Mahim — mahimm@berea.edu
