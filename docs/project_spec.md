# Bangladesh Climate Risk Atlas — Project Specification

Architecture reference for the Bangladesh Climate Risk Atlas.

---

## 1. Project Overview

The Bangladesh Climate Risk Atlas (BCRA) is a free, public, web-based geospatial analytics dashboard that exposes satellite-derived climate-risk indicators for every district of Bangladesh through a unified interface. The system fetches imagery and runs reductions on Google Earth Engine, presents results through a Streamlit web application, and is deployed as free public infrastructure on Streamlit Community Cloud.

Four climate indicators ship in the application:

1. Vegetation health (NDVI) from Sentinel-2.
2. Flood inundation extent from Sentinel-1 SAR.
3. Surface moisture (NDMI) from Sentinel-2.
4. Coastal salinity proxy from Sentinel-2 spectral combinations.

Each indicator is computed at the administrative-district level (FAO GAUL admin level 2), cached aggressively to minimize Earth Engine quota usage, and rendered in the user interface either as a time-series chart (NDVI, NDMI) or as a map overlay (flood, salinity). The system is bilingual (English plus Bangla labels) and operates without user accounts, telemetry, or any payment processing.

This document is the architectural reference for the system. It describes components, data flow, deployment topology, and the design decisions that shape implementation. It is intended as the first document a new contributor reads.

## 2. System Architecture

### 2.1 High-Level Topology

The system is structured as four loosely coupled layers:

```
+-------------------------------------------------------------------+
| Browser (any user, any device)                                    |
| - Renders HTML and JavaScript served by Streamlit                 |
+-------------------------------------------------------------------+
                          | HTTPS over public internet
                          v
+-------------------------------------------------------------------+
| Streamlit Community Cloud                                          |
| - Free public hosting tier                                         |
| - Watches GitHub main branch; auto-deploys on push                 |
| - Runs Python interpreter inside ephemeral Linux container         |
| - URL: bcra-project-bd.streamlit.app                               |
+-------------------------------------------------------------------+
                          | Python imports
                          v
+-------------------------------------------------------------------+
| Application code (this repository)                                 |
| - app.py    : Streamlit entry point and UI orchestration           |
| - atlas/    : Domain modules (NDVI, flood, etc.)                   |
| - data/     : Pre-computed static assets                           |
+-------------------------------------------------------------------+
                          | Earth Engine Python API
                          v
+-------------------------------------------------------------------+
| Google Earth Engine                                                |
| - Hosts Sentinel-1, Sentinel-2, JRC GSW, FAO GAUL                  |
| - Authenticates via service account on Cloud, OAuth on local dev   |
| - Executes reductions and returns small results                    |
+-------------------------------------------------------------------+
```

### 2.2 Request Lifecycle

When a user opens the live URL and selects a district:

1. Streamlit Cloud receives an HTTP request and runs `app.py` from top to bottom in a fresh Python process (or a warm one if the container is already running).
2. `init_ee()` from `atlas/ee_client.py` executes; on Cloud it reads the GCP service account credentials from `st.secrets` and initializes Earth Engine. On local development it falls through to user-OAuth credentials.
3. The cached district list is loaded (24-hour TTL via `@st.cache_data`).
4. The user picks a district from the selectbox widget.
5. For each indicator panel, the cached compute function is invoked. On a cache hit, the result returns instantly. On a miss, the function constructs an Earth Engine query graph and submits it via the EE Python API.
6. Earth Engine executes the query on Google's servers — pulling imagery from its archive, applying compositing and masking operations, and reducing over the district polygon — then returns small structured results (a list of monthly values for time-series indicators, or a tile URL for map indicators).
7. The Python code formats results: Plotly figures for charts, folium maps with EE tile layers for spatial outputs.
8. Streamlit serializes the components to HTML, JavaScript, and JSON payloads for the browser.

### 2.3 Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| `app.py` | UI orchestration, layout, widget state, Streamlit page configuration |
| `atlas/ee_client.py` | Earth Engine initialization with dual-mode authentication |
| `atlas/ndvi.py` | NDVI time-series computation (Sentinel-2 ingestion, masking, monthly composites) |
| `atlas/flood.py` | Sentinel-1 SAR flood detection |
| `atlas/moisture.py` | NDMI and surface-moisture time series |
| `atlas/salinity.py` | Coastal salinity proxy |
| `atlas/i18n.py` | English/Bangla string lookup |
| `data/` | Pre-computed static assets (boundaries, baselines, reference layers) |
| `notebooks/` | Sandbox experimentation, one notebook per indicator |
| `scripts/` | Smoke tests and operational utilities |

## 3. Technology Stack

### 3.1 Languages and Runtimes

- **Python 3.11** locally on Windows. Streamlit Cloud is currently running Python 3.14.4. The codebase is compatible with both. Avoid 3.12-only features.
- **JavaScript** is not directly written. Streamlit emits JS automatically; folium produces JS-bearing HTML via Jinja2 templates.

### 3.2 Core Libraries

| Library | Version Pin | Role |
|---------|-------------|------|
| `streamlit` | `>=1.30` | Web UI framework; turns Python script into hosted application |
| `earthengine-api` | `>=1.0` | Python client for Google Earth Engine |
| `pandas` | `>=2.2` | Tabular data structures for time-series outputs |
| `plotly` | `>=5.20` | Interactive charts (line, scatter) |
| `folium` | `>=0.20` | Leaflet-based interactive maps for spatial layers |
| `streamlit-folium` | `>=0.15` | Component for embedding folium in Streamlit |

Pinning policy: lower bounds only (`>=`), no upper bounds, no exact pins. This permits Streamlit Cloud's transitive resolver to pick compatible versions without lockfile maintenance. For a single-developer portfolio project this trades reproducibility risk for setup simplicity.

### 3.3 Justification for Major Choices

**Streamlit over Flask, FastAPI, or React.** Streamlit produces a hosted web application from a single Python script with no HTML, CSS, or JavaScript. For a single developer building a data-heavy dashboard on a one-week timeline, this trades flexibility for velocity. The cost is minor loss of layout control; the benefit is that the entire codebase is Python.

**Earth Engine over local geospatial processing.** Sentinel-1 GRD imagery is approximately 1 GB per scene; Sentinel-2 SR Harmonized is 0.5 to 1 GB. Processing several scenes per district per indicator requires terabytes of working storage and substantial compute. Earth Engine performs all of this on Google's infrastructure and returns kilobyte-scale results. This is the only architecture that makes the application feasible on a free hosting tier.

**Streamlit Community Cloud over self-hosted.** Self-hosting requires server administration, TLS, monitoring, and a payment method. Streamlit Cloud handles all of these for free at the cost of cold starts and shared infrastructure. For a portfolio project where uptime requirements are loose and total traffic is bounded, the trade-off is correct.

**Service account authentication over user OAuth in production.** OAuth requires an interactive browser sign-in flow that does not exist in a Streamlit Cloud container. Service accounts are the standard non-human identity for headless workloads in Google Cloud and are the documented path for Earth Engine in deployed applications.

## 4. Earth Engine Integration

### 4.1 Authentication Modes

The `init_ee()` function in `atlas/ee_client.py` is dual-mode:

- **Cloud mode (Streamlit Cloud):** Reads `st.secrets["gcp_service_account"]` (a TOML-formatted block containing the full service account JSON), constructs `ee.ServiceAccountCredentials`, and initializes Earth Engine against project `earth-engine-project-495404`.
- **Local mode (development laptop):** When `st.secrets` is absent or the secrets key is not present, the function falls through to bare `ee.Initialize(project="earth-engine-project-495404")`, which uses credentials cached by `earthengine authenticate` in the developer's home directory.

The function is idempotent. Repeated calls do not reinitialize.

### 4.2 Project Configuration

- **Google Cloud project ID:** `earth-engine-project-495404`
- **Project type:** Non-commercial / academic (eligible via Berea College affiliation)
- **Quota tier:** Earth Engine Community Tier (free, default for non-commercial)
- **Service account:** `streamlit-runner@earth-engine-project-495404.iam.gserviceaccount.com`
- **Service account roles:** `Earth Engine Resource Viewer`, `Service Usage Consumer`

The two-role requirement is non-obvious. `Earth Engine Resource Viewer` alone allows the service account to read EE assets but not to use the project's API quota. `Service Usage Consumer` permits API consumption. Without both, EE calls return HTTP 403 with `Caller does not have required permission to use project ... Grant the caller the roles/serviceusage.serviceUsageConsumer role`.

### 4.3 Quota and Concurrency Considerations

Earth Engine's Community Tier has known concurrency limits that surface as `429 Too Many concurrent aggregations` when many `reduceRegion` calls run in parallel. The original NDVI implementation hit this limit when constructing a `FeatureCollection` of 24 monthly features each containing a deferred `reduceRegion`; EE evaluated all 24 in parallel server-side and exceeded the cap.

The current production NDVI pipeline avoids this by stacking N monthly composites into a single multi-band image and performing one `reduceRegion` call. This is the canonical pattern for time-series workloads on Earth Engine and is what new indicator pipelines should use.

### 4.4 Catalog Datasets in Use

| Dataset ID | Use | Notes |
|------------|-----|-------|
| `COPERNICUS/S2_SR_HARMONIZED` | NDVI, NDMI, salinity | Sentinel-2 Level-2A, harmonized for the 2022 baseline shift |
| `COPERNICUS/S1_GRD` | Flood detection | Sentinel-1 Ground Range Detected; VV polarization for water |
| `JRC/GSW1_4/GlobalSurfaceWater` | Permanent water mask | Occurrence band, threshold > 50% defines permanent water |
| `FAO/GAUL/2015/level2` | District boundaries inside EE | Used for `filterBounds` and `reduceRegion` geometry |

## 5. Data Pipeline Designs

### 5.1 NDVI

Module: `atlas/ndvi.py`

Pipeline:

1. **District resolution.** Filter `FAO/GAUL/2015/level2` by `ADM0_NAME == 'Bangladesh'` and `ADM2_NAME == <district>`; take `.first()` and extract geometry.
2. **Date window construction.** Compute month starts from `end_date - (months - 1)` to `end_date` inclusive.
3. **Sentinel-2 ingestion.** Filter `COPERNICUS/S2_SR_HARMONIZED` by district bounds, full date range, and `CLOUDY_PIXEL_PERCENTAGE < 60`.
4. **Cloud masking.** For each scene, mask cloud and cirrus pixels using QA60 bits 10 and 11. Divide by 10000 to convert from packed integer reflectance to physical reflectance (0 to 1). Preserve `system:time_start` metadata.
5. **NDVI band computation.** Apply `normalizedDifference(['B8', 'B4'])` to each masked image, rename the result to `NDVI`.
6. **Monthly compositing with empty-month handling.** For each month, create a band named `ndvi_YYYY_MM`. Use `ee.Algorithms.If` to handle empty months: if the monthly collection has zero scenes, return a fully-masked constant image; otherwise return the mean of the collection's NDVI.
7. **Stacked-band reduction.** Concatenate all N monthly bands into one `ee.Image` via `ee.Image.cat`, then call `reduceRegion` once with `Reducer.mean()` at scale 100m. This is a single Earth Engine round-trip, not N.
8. **Client-side framing.** Convert the returned dictionary into a pandas DataFrame with columns `date` (datetime64) and `ndvi` (float64, NaN for empty months). Sort ascending.

Public API:
```python
def ndvi_timeseries(
    district_name: str,
    months: int = 24,
    end_date: ee.Date | None = None,
) -> pd.DataFrame
```

### 5.2 Flood Detection

Module: `atlas/flood.py` (reference notebook: `notebooks/02_flood_sandbox.ipynb`)

Pipeline:

1. **District geometry.** Same as NDVI.
2. **Date windows.** Two windows: a pre-flood baseline (typically 2-3 weeks before the event) and a flood window covering the event period.
3. **Sentinel-1 ingestion.** Filter `COPERNICUS/S1_GRD` by district bounds, with `instrumentMode == 'IW'`, polarization list containing `'VV'`, and orbit pass `'DESCENDING'`. Descending pass is the conventional choice for Bangladesh flood mapping per published literature.
4. **Median compositing.** Reduce both windows to median composites of the VV band. Median reduces SAR speckle noise more effectively than mean.
5. **Thresholding.** Apply a threshold of -16 dB to the flood-window VV composite. Pixels below -16 dB are classified as water. This threshold is validated for Bangladesh in Thomas et al. (2019), MDPI Remote Sensing 11:1581.
6. **Permanent-water masking.** Load `JRC/GSW1_4/GlobalSurfaceWater`, select the `occurrence` band, threshold at `> 50` to define permanent water, `unmask(0)` to remove the dataset's no-data mask. Apply via `flood_water.updateMask(permanent_water.eq(0))`. The `updateMask` route is required; alternatives using `.Not()` or `.subtract()` produce projection-resampling artifacts that under-count flood extent by 70% or more.
7. **Area accounting.** Compute area in square kilometers via `image.multiply(ee.Image.pixelArea()).divide(1e6)` summed within the district polygon.

Validation results (Sylhet, 2024 monsoon event):
- Flood-only extent: 1,301.5 km² (37.4% of district area)
- Pre-flood baseline water: 193.5 km²
- Permanent water (JRC) within district: 102.9 km²
- Dry-season false-positive control (February-March 2024): 27.9 km² (0.8% of district)
- Contrast ratio: 47x (flood vs. dry-season)

### 5.3 NDMI

Module: `atlas/moisture.py`

Structurally similar to NDVI: same Sentinel-2 ingestion, same cloud masking, same monthly compositing. The band formula changes from `(B8 - B4) / (B8 + B4)` to `(B8 - B11) / (B8 + B11)`.

### 5.4 Coastal Salinity

Module: `atlas/salinity.py`

Restricted to the 19 coastal districts (hard-coded list in `data/coastal_districts.json`). Uses the Bouaziz (2011) salinity index `SI = √(B2 × B4)` over Sentinel-2 SR Harmonized imagery. Output is two seasonal means (dry-season and wet-season) per district, not a time series. The methodology page documents that this is a visible-band brightness proxy, not a calibrated soil-EC measurement.

## 6. Module Structure

```
bcra-project/
|-- app.py                      Streamlit entry point; UI orchestration
|-- requirements.txt            pip dependency list (lower bounds only)
|-- runtime.txt                 Python version pin (advisory; cloud may override)
|-- README.md                   Public-facing project description
|-- LICENSE                     MIT
|-- .gitignore                  Excludes secrets, logs, caches, HTML artifacts
|-- .streamlit/
|   `-- secrets.toml            NOT committed; for local Cloud-mode testing
|-- atlas/                      Python package for domain logic
|   |-- __init__.py             Empty package marker
|   |-- ee_client.py            Earth Engine init (dual-mode)
|   |-- ndvi.py                 Sentinel-2 NDVI time series
|   |-- moisture.py             Sentinel-2 NDMI time series
|   |-- flood.py                Sentinel-1 SAR flood detection
|   |-- salinity.py             Sentinel-2 Bouaziz salinity index
|   |-- exports.py              CSV serialization helpers
|   |-- i18n.py                 English / Bangla string dictionaries
|   `-- ui.py                   Shared sidebar chrome and footer
|-- pages/
|   `-- methodology.py          Methodology page (Streamlit multi-page)
|-- data/
|   |-- coastal_districts.json  Coastal district names (FAO GAUL spelling)
|   `-- strings.json            Bilingual i18n dictionary
|-- notebooks/
|   |-- 01_ndvi_sandbox.ipynb   NDVI sandbox; Rangpur and Khulna validation
|   `-- 02_flood_sandbox.ipynb  Sentinel-1 flood sandbox; Sylhet 2024 validation
|-- scripts/
|   |-- verify_ndvi.py          Smoke test for atlas/ndvi.py
|   |-- verify_ndmi.py          Smoke test for atlas/moisture.py
|   |-- verify_flood.py         Smoke test for atlas/flood.py
|   |-- verify_salinity.py      Smoke test for atlas/salinity.py
|   |-- verify_exports.py       Smoke test for atlas/exports.py
|   `-- verify_i18n.py          Smoke test for atlas/i18n.py
`-- docs/
    `-- project_spec.md         This document
```

## 7. Caching Strategy

Caching is a first-class concern, not a performance optimization. Earth Engine queries take 5 to 30 seconds; without caching, every district selection would be unusable.

### 7.1 Streamlit Compute Cache (`@st.cache_data`)

- **District list:** TTL 24 hours. The list of 64 Bangladesh districts changes never; we cache for 24 hours as a defensive bound.
- **Per-district NDVI:** TTL 1 hour. New Sentinel-2 imagery becomes available roughly every 5 days; sub-hour freshness is unnecessary.
- **Per-district flood:** TTL 6 hours. Sentinel-1 revisits every 6 to 12 days; finer granularity is meaningless.

Cache keys are derived from function arguments. Two users selecting the same district both hit the cache, so quota usage scales with unique district selections, not page views.

### 7.2 Pre-computed Static Assets

Assets that do not depend on user interaction or current data should be pre-computed and committed to `data/`:

- Coastal district name list (`coastal_districts.json`)
- Bilingual i18n strings (`strings.json`)

Pre-computed assets are never regenerated at request time. Updates happen offline on the developer's machine and are committed.

### 7.3 Earth Engine Tile Cache

For map layers, Earth Engine returns Map IDs whose tile URLs are served from Google's edge cache. Tile fetches do not count against EE compute quota. Rendering the same flood layer to many users is essentially free after the initial computation.

## 8. Deployment Architecture

### 8.1 Hosting

- **Platform:** Streamlit Community Cloud (free tier).
- **Trigger:** Watches `mushfiqmahim/bcra-project` `main` branch via GitHub OAuth.
- **Behavior:** On every push to `main`, Streamlit Cloud rebuilds the container in approximately 30 to 90 seconds. Build failures keep the previous version live; users do not see broken builds.
- **URL:** https://bcra-project-bd.streamlit.app
- **Cold start:** 10 to 30 seconds when no recent traffic.

### 8.2 Build Pipeline

1. Streamlit Cloud detects the GitHub push.
2. Container is provisioned; Python interpreter installed.
3. `requirements.txt` is resolved using `uv pip install`.
4. Container starts; Uvicorn serves the Streamlit app on port 8501.
5. First user request triggers `app.py` execution.

### 8.3 Rollback

Bad deploys are reverted by:

```
git revert HEAD
git push
```

Streamlit Cloud rebuilds with the prior state. No history rewriting; no force-push.

## 9. Security

### 9.1 Service Account Credentials

The Earth Engine service account JSON is sensitive. Treatment:

- **Storage on developer machine:** `C:\Users\mahimm\OneDrive - Berea College\Documents\bcra-secrets\` — outside the repository root.
- **Storage on Streamlit Cloud:** Streamlit Cloud's Secrets UI (Settings → Secrets) under TOML key `[gcp_service_account]`. Streamlit's secrets store is not visible in build logs or app logs.
- **Repository exposure:** `.gitignore` excludes `*.json` patterns within the repo root. The `bcra-secrets` directory is outside the repo entirely.
- **Rotation policy:** Any time a key is exposed (logged conversation, screenshot, file shared outside the intended path), the key is treated as compromised and rotated immediately. This has happened once during development; the prior key is revoked.

### 9.2 Public Repository Surface

The repository is public. This means:

- No secrets are ever committed.
- Configuration that contains identifiers but not secrets (project ID, service account email) is acceptable to commit.
- Code review for accidental exposure happens on every commit via `git status` inspection before `git add`.

### 9.3 Streamlit Cloud Trust Model

Streamlit Cloud reads from a public GitHub repository and runs the code in an isolated container. Secrets are injected via an environment-equivalent mechanism. The container itself is not directly addressable by users; only the served HTTP application is exposed.

## 10. Known Limitations

The following limitations are inherent to the design and are documented for transparency.

### 10.1 NDVI

- **Cloud cover during monsoon.** Sentinel-2 is optical and is blocked by clouds. June through September Bangladesh has heavy cloud cover; some monthly composites will return NaN. The UI surfaces this honestly with gaps in the time series rather than interpolation.
- **Mixed land cover.** NDVI is a district-level mean across all green surfaces. It cannot distinguish crops from natural vegetation, nor identify specific crop types.

### 10.2 Flood Detection

- **Threshold sensitivity.** The -16 dB threshold is a population-level value validated for Bangladesh. It can produce false positives over tarmac, parking lots, and wet rice paddies during transplanting (which appear water-like to SAR).
- **Median composite hides peak.** The median across the flood window understates the true peak inundation. A user looking at the May 25 - June 30 composite for Sylhet sees the typical inundation across that period, not the worst day.
- **JRC permanent water mask is conservative.** The 50% occurrence threshold excludes seasonal water (haor edges that are wet 30 to 50% of months) from the permanent layer. Our flood-only count may include normal seasonal expansion of the haor. The dry-season control test confirms this is a small contribution (under 1% of district area).
- **Projection-resampling artifacts.** Operations that mix images at different native projections (Sentinel-1 at 10m UTM versus JRC GSW at 30m EPSG:4326) require careful method selection. `updateMask` and `where` produce correct results; `Not()`-based and `subtract`-based formulations of the same logical operation produce incorrect results due to fractional resampling values.

### 10.3 General

- **Free hosting cold starts.** The first user request after a period of inactivity takes 10 to 30 seconds. Universal across free hosting tiers.
- **Single-developer pace.** No staging environment; pushes go directly to production. The cost is acceptable given Streamlit Cloud preserves the prior version on bad deploys.

## 11. Future Extensibility

### 11.1 Indicator Additions

Each new indicator is a module under `atlas/` with a public function returning either a DataFrame (time series) or an `ee.Image` plus Map ID URL (spatial). Wiring into `app.py` requires adding a panel that calls the function and renders the output.

Candidate indicators:
- Cyclone storm-surge risk (bathymetry plus elevation)
- River-bank erosion (Sentinel-2 time-series shoreline analysis)
- Heat stress (ECMWF ERA5 reanalysis)

### 11.2 Algorithm Refinement

Current flood detection uses fixed-threshold classification. Production-grade alternatives:

- Random forest classifier on VV, VH, and incidence-angle features (Thomas et al. 2019 algorithm)
- Otsu adaptive thresholding per-scene
- Change detection via z-score of pre-flood vs flood-window backscatter

These can be swapped behind the same public API in `atlas/flood.py` without UI changes.

### 11.3 Geographic Expansion

Architecture is country-agnostic. Adding Bhutan, Nepal, or Myanmar requires:

- New boundary dataset (still FAO GAUL, different `ADM0_NAME` filter)
- New coastal district list for the salinity panel (or omission for landlocked countries)
- Additional translations in `atlas/i18n.py`

### 11.4 API Surface

A future REST endpoint could expose the same per-district indicators as JSON. Separate module that imports `atlas/*` and exposes via FastAPI or Flask. Streamlit and JSON API can coexist.

---

*End of architectural specification. This document is a living artifact; update it whenever architectural decisions change.*
