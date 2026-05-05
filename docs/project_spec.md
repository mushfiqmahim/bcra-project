# Bangladesh Climate Risk Atlas — Project Specification

**Repository:** `mushfiqmahim/bcra-project`
**Live application:** https://bcra-project-bd.streamlit.app
**Status:** Phase A complete (scaffold and live deployment). Phase B in planning.
**Document version:** 1.0 — Initial specification.
**Maintainer:** Mushfiq Mahim (mahimm@berea.edu)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [The Problem](#2-the-problem)
3. [Target Users](#3-target-users)
4. [Technical Architecture](#4-technical-architecture)
5. [How the Tools Fit Together](#5-how-the-tools-fit-together)
6. [Repository Structure](#6-repository-structure)
7. [Data Sources](#7-data-sources)
8. [Climate Risk Indicators](#8-climate-risk-indicators)
9. [Build Phases](#9-build-phases)
10. [Role of Claude Code](#10-role-of-claude-code)
11. [Expected Outputs Per Phase](#11-expected-outputs-per-phase)
12. [Technical Risks and Debugging](#12-technical-risks-and-debugging)
13. [Deployment Plan](#13-deployment-plan)
14. [Future Expansion](#14-future-expansion)
15. [Glossary](#15-glossary)

---

## 1. Project Overview

The Bangladesh Climate Risk Atlas (BCRA) is a free, public, web-based dashboard that combines four satellite-derived climate risk signals into one interface, organized at the district level for all of Bangladesh. The four signals are vegetation health, drought stress, flood inundation, and coastal salinity exposure.

The tool is delivered as a single-page web application accessible from any browser, with a bilingual interface (English plus basic Bangla labels). It does not require user accounts. All processing happens on demand using Google's Earth Engine cloud compute platform; the application itself is a thin Python program that orchestrates queries, formats results, and renders charts and maps.

The project is intentionally narrow in scope. It is not a farmer advisory app. It is not a forecasting service. It is not a research-grade analytical platform. It is a public-good visualization layer over publicly available satellite data, designed to make existing scientific signals accessible to non-experts.

---

## 2. The Problem

Bangladesh faces a unique combination of climate risks: monsoon flooding from upstream rivers, cyclone-driven storm surge along the Bay of Bengal, drought in the northwest dry season, and accelerating soil salinity in the southwest coastal belt. These risks intersect with smallholder agriculture, where roughly 80 percent of farmers operate plots smaller than 2 hectares and where livelihoods are tightly coupled to seasonal weather.

The data needed to monitor these risks already exists. Sentinel-1 and Sentinel-2 satellites image the country every few days. The European Space Agency provides this imagery free of charge. Google Earth Engine hosts the imagery and provides cloud compute capacity at no cost for non-commercial users. Academic literature has validated specific algorithms for flood detection, drought monitoring, and salinity estimation in the Bangladesh context.

Despite this, no free public dashboard integrates these signals at the district level for non-expert users. The existing options fall into one of three categories:

- **Government services** (BAMIS, FFWC, BMD) provide raw data and forecasts but each agency operates a separate portal with a different audience, different UX, and limited integration. They are designed for agricultural officers and disaster officials, not for public consumption.
- **Commercial platforms** (Farmonaut, OnGeo, GEOBIS) offer integrated views but operate on B2B subscription models. They do not publish free dashboards; the business model requires lead capture and paid licensing.
- **Academic research code** (peer-reviewed Sentinel-1 SAR flood mapping algorithms, salinity modeling notebooks, field boundary detection networks) is correct and high-quality, but lives in research repositories and PDFs. None of it is presented as an end-user web tool.

The gap that BCRA fills: a free, public, multi-hazard, district-level web interface that translates validated academic methods into something a journalist, NGO worker, graduate student, or extension officer can browse on a phone in two minutes.

---

## 3. Target Users

The application is designed primarily for these user groups, in rough order of expected adoption:

- **Researchers and graduate students** in agriculture, climate science, and development economics who need quick regional snapshots without writing Earth Engine code.
- **Journalists** covering climate, agriculture, and disaster topics in Bangladesh who need credible, citable, real-time data views.
- **Local NGOs and development organizations** working on food security, climate adaptation, and disaster preparedness.
- **Civic developers and data-journalism teams** who can use the site directly and use the underlying open-source code as a starting point for their own analyses.
- **Agricultural extension officers and NGO field staff** who can show district-level visuals to farmers in the field on a phone.

The application is **not** designed for the following users, even though they may benefit indirectly:

- Individual smallholder farmers as primary users — that audience is already served by SMS-based services (GEOBIS, government extension), voice-message systems, and field officers; an English-and-basic-Bangla web dashboard is not the right interface.
- Disaster response operators making real-time decisions during active flood events — the data refresh cadence (Sentinel-1 revisits every 6 to 12 days) is too slow for live response, and FFWC remains the authoritative source.
- Commercial agribusinesses needing field-level precision — those buyers need higher-resolution imagery and field-level subscriptions from commercial vendors.

Being explicit about non-users is a design constraint. It prevents scope creep and keeps UX decisions clean.

---

## 4. Technical Architecture

### 4.1 High-Level View

The application follows a four-layer architecture:

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (any user)                                         │
│    ↓ HTTPS                                                  │
├─────────────────────────────────────────────────────────────┤
│  Streamlit Community Cloud (free public hosting)            │
│    Runs the Python app in a managed container               │
│    URL: bcra-project-bd.streamlit.app                       │
│    ↓ Python imports                                         │
├─────────────────────────────────────────────────────────────┤
│  Application code (this repo)                               │
│    app.py                — UI orchestration                 │
│    atlas/                — domain modules (NDVI, flood, …)  │
│    data/                 — pre-computed static assets       │
│    ↓ Earth Engine Python API                                │
├─────────────────────────────────────────────────────────────┤
│  Google Earth Engine (server-side compute)                  │
│    Hosts Sentinel-1, Sentinel-2, JRC Surface Water, GAUL    │
│    Executes user queries against petabyte-scale archives    │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Data Flow on a Single User Request

When a user opens the app and selects a district:

1. The Streamlit container receives an HTTP request and runs the Python script `app.py` from top to bottom.
2. The script reads the selected district code from Streamlit's session state.
3. For each of the four indicators, the script calls a function in the `atlas/` package.
4. Each function constructs an Earth Engine query — a chain of method calls on `ee.ImageCollection` and `ee.Image` objects — and submits it to Google's servers via the Earth Engine Python API.
5. Google's servers execute the query against the relevant satellite imagery archive and return small structured results: a list of monthly NDVI values, a flood map as a Map ID URL, etc.
6. The Python script formats the results into Plotly charts and folium maps.
7. Streamlit serializes the rendered components into HTML and JavaScript and ships the response back to the browser.
8. The browser displays the dashboard. Subsequent interactions (changing the district, toggling language) trigger Streamlit reruns, but cached results are reused.

### 4.3 Key Architectural Decisions

**Earth Engine for compute, not local processing.** Sentinel-1 and Sentinel-2 imagery is too large to download and process on a free hosting tier. Earth Engine performs the computation on Google's infrastructure and returns small results (numbers, polygons, tile URLs). The application never handles raw imagery.

**Streamlit for UI, not a custom web framework.** Streamlit lets us write the entire user interface in Python without HTML, CSS, or JavaScript. For a one-developer project on a one-week timeline, this trades flexibility for velocity. The cost is some loss of design control; the benefit is that the entire codebase remains in one language.

**Service account authentication, not user OAuth.** The deployed application uses a Google Cloud service account to authenticate with Earth Engine. This is required because the standard user-OAuth flow expects an interactive browser sign-in, which is not available in a Streamlit Cloud container.

**Caching as a first-class concern.** Earth Engine queries take 5 to 30 seconds. Without caching, every user interaction would feel broken. The application uses Streamlit's `@st.cache_data` decorator aggressively and pre-computes static assets (district boundaries, baseline composites) into the repository as GeoJSON or Parquet files.

**Pre-computed static layers in the repo.** District boundaries do not change. The 5-year NDVI baseline does not change daily. Storing these as committed files in `data/` removes them from the per-request critical path.

---

## 5. How the Tools Fit Together

### 5.1 Streamlit

Streamlit is a Python library that turns a Python script into a web application. Every widget (text input, selectbox, slider) is a single function call that both renders an HTML element and returns the user's input. The entire application is one or more Python files; Streamlit handles the rest.

In this project, Streamlit:
- Renders the page layout (title, sidebar, four panels)
- Provides the district selector widget and language toggle
- Caches results between user interactions
- Serves the application to browsers

We do not write HTML, CSS, JavaScript, or HTTP routing. We do not define endpoints. We do not run a server; Streamlit Community Cloud runs it for us.

### 5.2 GitHub

GitHub stores the source code and serves as the deployment trigger.

- **Source of truth:** All code lives in `github.com/mushfiqmahim/bcra-project`. The local laptop, Streamlit Cloud's container, and any contributor's clone all derive from this repository.
- **Version control:** Every change is a commit with a message. We can revert mistakes, audit history, and branch for experimental features.
- **Deployment trigger:** Streamlit Cloud watches the `main` branch. When we push, Streamlit Cloud rebuilds the container and redeploys within roughly one minute. There is no separate deploy step.

We use GitHub through standard `git` command-line operations: `git add`, `git commit`, `git push`. We do not use GitHub Actions, GitHub Pages, or other GitHub features for the core flow.

### 5.3 Google Earth Engine (GEE)

Earth Engine is Google's planet-scale geospatial analysis platform. It hosts decades of satellite imagery (Sentinel, Landsat, MODIS, and others), exposes a Python and JavaScript API, and executes computations on Google's servers.

In this project, Earth Engine:
- Stores Sentinel-1 (radar) and Sentinel-2 (optical) imagery for Bangladesh from 2015 to present
- Stores administrative boundaries (FAO GAUL dataset) for districts globally including Bangladesh
- Stores the JRC Global Surface Water dataset, used to mask permanent water bodies out of flood detection
- Executes our queries: cloud masking, NDVI computation, monthly compositing, flood detection thresholding, and zonal statistics by district

We interact with Earth Engine exclusively through the `earthengine-api` Python package. We never download imagery; we describe computations and receive small results.

### 5.4 Claude Code

Claude Code is a command-line agent that operates in the terminal. It can read project files, edit them, run shell commands, and observe the results. It is paired with Claude Opus 4.7 for reasoning.

In this project, Claude Code:
- Helps draft new functions when given a precise specification
- Helps debug Earth Engine errors by reading the code, running it, and proposing fixes
- Helps refactor exploratory notebook code into clean modules
- Helps write documentation and READMEs

Claude Code does not replace the developer's judgment. The developer is responsible for scoping each task tightly, verifying that suggestions actually run, and rejecting suggestions that introduce unnecessary complexity or hallucinated APIs.

### 5.5 The Connection Between All Four

```
Developer (Mushfiq) writes a function in VS Code with help from Claude Code
   ↓
Developer runs `streamlit run app.py` locally; verifies it works
   ↓
Developer commits and pushes to GitHub
   ↓
Streamlit Cloud detects the push, rebuilds the container
   ↓
Streamlit Cloud starts the new app, which authenticates to Google Earth Engine
   ↓
First user visits the live URL; the new code serves them
```

This loop runs many times per day during the build week.

---

## 6. Repository Structure

The current repository has been cleaned up in Phase A. The target structure for the full project is below.

```
bcra-project/
├── app.py                          # Streamlit entry point; UI orchestration
├── requirements.txt                # Python dependencies
├── runtime.txt                     # Python version pin (3.12)
├── README.md                       # Public-facing project description
├── LICENSE                         # MIT
├── .gitignore                      # Python, venv, secrets, OS files
│
├── .streamlit/
│   ├── config.toml                 # Streamlit theming (colors, fonts)
│   └── secrets.toml                # NOT committed; contains GCP service account JSON
│
├── atlas/                          # Python package for domain logic
│   ├── __init__.py
│   ├── ee_client.py                # Earth Engine initialization (local + cloud)
│   ├── districts.py                # GADM/FAO GAUL boundary loader, district list
│   ├── ndvi.py                     # Sentinel-2 NDVI time series and anomaly detection
│   ├── moisture.py                 # NDMI computation, drought stress proxy
│   ├── flood.py                    # Sentinel-1 SAR flood detection
│   ├── salinity.py                 # Coastal salinity proxy index
│   ├── plots.py                    # Plotly chart helpers
│   ├── maps.py                     # folium map helpers
│   └── i18n.py                     # English/Bangla string lookup
│
├── data/
│   ├── gadm_bd_admin2.geojson      # Pre-downloaded district boundaries
│   ├── coastal_districts.json      # List of coastal district codes
│   └── ndvi_baseline_2019_2023.parquet  # Pre-computed 5-year NDVI baseline (later phase)
│
├── notebooks/
│   ├── 01_ndvi_sandbox.ipynb       # Exploration notebook for Phase C
│   ├── 02_flood_sandbox.ipynb      # Exploration notebook for Phase D
│   ├── 03_moisture_sandbox.ipynb   # Exploration notebook for Phase E
│   └── 04_salinity_sandbox.ipynb   # Exploration notebook for Phase F
│
└── docs/
    ├── project_spec.md             # This document
    ├── methodology.md              # Public-facing methodology (citations)
    ├── data_sources.md             # Detailed data source documentation
    └── deployment.md               # How to deploy from a fresh clone
```

### 6.1 Why This Structure

- **Single entry point at the root.** Streamlit Cloud expects `app.py` (or `streamlit_app.py`) at the root by default. Keeping the entry point thin and the logic in `atlas/` makes the entry point easy to read.
- **Domain modules in a Python package.** Each climate indicator gets its own module. This forces clean separation of concerns — the NDVI logic does not know about the salinity logic, and vice versa. A new contributor can read one file and understand one indicator.
- **Static assets in `data/`.** Anything that does not change (boundaries, baselines) lives here. The application reads them from disk, not from Earth Engine, on every request.
- **Notebooks in `notebooks/`.** These are exploration and validation tools. They are not deployed; they exist so we can debug Earth Engine queries interactively before promoting them to `atlas/` modules.
- **Documentation in `docs/`.** The project spec, methodology, data sources, and deployment notes live here, separate from the README which stays focused on quick orientation.

### 6.2 What Each File in `atlas/` Does

| File | Responsibility |
|---|---|
| `ee_client.py` | Initialize Earth Engine for local development (user OAuth) and cloud deployment (service account). One function: `init_ee()`. |
| `districts.py` | Load GADM Bangladesh boundaries. Provide `list_districts()` returning name + code, and `get_geometry(code)` returning an `ee.Geometry`. |
| `ndvi.py` | Compute Sentinel-2 NDVI monthly time series for a district. Compare current value against a baseline. Return a pandas DataFrame. |
| `moisture.py` | Compute NDMI (moisture index) and a simple drought-stress composite for a district. Return a pandas DataFrame. |
| `flood.py` | Sentinel-1 SAR flood detection. Threshold VV polarization, mask permanent water using JRC dataset, return a flood map as an Earth Engine Map ID. |
| `salinity.py` | Spectral salinity index for coastal districts only. Return a current value and seasonal context. |
| `plots.py` | Wrappers around Plotly that produce the four panel charts with consistent styling. |
| `maps.py` | Wrappers around folium that produce the country-level choropleth and district-level overlays. |
| `i18n.py` | Dictionary of UI strings in English and Bangla. One function: `t(key, lang)`. |

---

## 7. Data Sources

All data sources are free, publicly accessible, and used within their stated terms of use.

### 7.1 Satellite Imagery

| Source | Provider | Resolution | Revisit | Use |
|---|---|---|---|---|
| Sentinel-2 Level-2A SR Harmonized | ESA Copernicus, hosted on Earth Engine as `COPERNICUS/S2_SR_HARMONIZED` | 10–60 m | 5 days (cloud permitting) | NDVI, NDMI, salinity proxy |
| Sentinel-1 GRD | ESA Copernicus, hosted on Earth Engine as `COPERNICUS/S1_GRD` | 10 m | 6–12 days | Flood detection (radar penetrates clouds) |

Both are free under the Copernicus open data license. Earth Engine hosts them at no cost for non-commercial users.

### 7.2 Boundaries

| Source | Provider | Use |
|---|---|---|
| FAO GAUL 2015 Level 2 | FAO via Earth Engine: `FAO/GAUL/2015/level2` | District boundaries inside Earth Engine queries |
| GADM v4.1 admin level 2 | gadm.org | Pre-downloaded GeoJSON for client-side rendering in folium |

We use FAO GAUL inside Earth Engine because it is already on the platform and avoids upload steps. We use GADM for the local map rendering because it is more topologically clean.

### 7.3 Auxiliary Datasets

| Source | Provider | Use |
|---|---|---|
| JRC Global Surface Water | EC JRC via Earth Engine: `JRC/GSW1_4/GlobalSurfaceWater` | Mask permanent water bodies out of flood detection |
| NASA POWER | NASA via API at `power.larc.nasa.gov/api` | Daily temperature and precipitation for context (optional, later phase) |

### 7.4 No User-Generated Data

The application does not collect, store, or process any user-generated data. There are no accounts, no telemetry beyond Streamlit Cloud's default anonymous request counts, and no user uploads. This is a deliberate constraint: it eliminates data protection obligations, simplifies the privacy story, and reduces the attack surface.

---

## 8. Climate Risk Indicators

Each indicator is independently computed and rendered in its own panel. The four indicators were chosen based on a review of academic literature on Bangladesh-specific remote sensing and consultation with the build guide's gap analysis.

### 8.1 Vegetation Health (NDVI)

**What it measures:** The Normalized Difference Vegetation Index (NDVI) is computed from the red and near-infrared bands of Sentinel-2 imagery. Values range from -1 to +1; healthy vegetation typically reads 0.5 to 0.9. The index is a proxy for green biomass and crop vigor.

**Formula:** `NDVI = (NIR - RED) / (NIR + RED)`. In Sentinel-2 bands, this is `(B8 - B4) / (B8 + B4)`. The Earth Engine method `image.normalizedDifference(['B8', 'B4'])` computes this in one call.

**What we display:** A 24-month time series of monthly mean NDVI for the selected district, with the current value highlighted and compared against the same calendar month averaged over the previous 5 years (the baseline). An anomaly flag triggers when the current value is more than one standard deviation below the 5-year mean for that month.

**Caveats:** NDVI is sensitive to cloud cover. During monsoon months, cloud-free imagery may be sparse. The application uses a cloud mask based on the QA60 band and shows confidence based on the number of clean observations available. NDVI cannot distinguish crops from natural vegetation; in mixed land cover, the value reflects the average of all green surfaces in the district.

### 8.2 Drought and Moisture Stress (NDMI)

**What it measures:** The Normalized Difference Moisture Index (NDMI) uses the near-infrared and shortwave-infrared bands to estimate vegetation water content. It complements NDVI: NDVI tells us if vegetation is green, NDMI tells us if it is water-stressed.

**Formula:** `NDMI = (NIR - SWIR) / (NIR + SWIR)`. In Sentinel-2 bands, this is `(B8 - B11) / (B8 + B11)`.

**What we display:** A parallel time series to NDVI. We also compute a simple drought-stress composite: `drought_score = -1 * (NDVI_anomaly + NDMI_anomaly) / 2`. Higher scores indicate vegetation that is both browning and drying — a stronger drought signal than either index alone.

**Caveats:** SWIR is also affected by clouds and shadows. The application uses the same cloud mask as NDVI. NDMI does not measure soil moisture directly; it measures canopy moisture, which is a leading indicator of agricultural drought stress but not the same as root-zone water deficit.

### 8.3 Flood Inundation (Sentinel-1 SAR)

**What it measures:** Synthetic Aperture Radar (SAR) emits microwave signals that bounce off the Earth's surface. Smooth surfaces (open water, calm flooded fields) reflect the signal away from the satellite, producing low backscatter values. Rough surfaces (vegetation, buildings, dry soil) scatter the signal back, producing high values. By thresholding the backscatter, we can detect water.

**Algorithm:** We use the VV polarization of Sentinel-1 GRD imagery. For a given month:

1. Filter the Sentinel-1 collection to the district and date range.
2. Compute a median composite to reduce speckle noise.
3. Convert to dB scale.
4. Apply a threshold (typically -16 dB) to classify pixels as water or non-water.
5. Mask out the permanent water bodies using the JRC Global Surface Water dataset (occurrence > 50 percent over 1984–2021).
6. The remaining water pixels are inferred flood pixels.

**What we display:** A map layer for the most recent month showing flood pixels in cyan over a basemap. For coastal and flood-prone districts, we also show the same layer for the most recent monsoon peak (typically late August).

**Caveats:** SAR thresholding produces false positives in three known cases: (a) tarmac and other smooth artificial surfaces sometimes read as water; (b) wet rice paddies during transplanting can appear as water and inflate flood estimates; (c) calm inland water bodies missed by the JRC permanent-water mask. The methodology page documents all three. A future phase may incorporate a machine-learning classifier (random forest on VV/VH/incidence-angle features, following Thomas et al. 2019) to reduce false positives.

### 8.4 Coastal Salinity (Spectral Proxy)

**What it measures:** Soil salinity in coastal Bangladesh has been correlated with specific spectral signatures in Landsat and Sentinel-2 imagery. Sarkar et al. (2023, Scientific Reports) and others have published spectral combinations that estimate salinity levels from optical bands.

**Algorithm:** For coastal districts only (a hard-coded list of 19 districts in southern Bangladesh), we compute a salinity index based on a spectral combination from the literature. The exact formula is selected from Sarkar et al. 2023 or one of its citations.

**What we display:** A current snapshot value and a seasonal context (compare to the same season in prior years). We render this as a single number with a color-coded category (low, moderate, high) plus a brief textual interpretation.

**Caveats:** This is a proxy, not a direct measurement. Ground-truth electrical conductivity (EC) values from soil samples are the gold standard; we cannot match that accuracy. The methodology page is explicit about this limitation. The salinity panel is deliberately restricted to coastal districts where the literature has validated the approach; it is not displayed for inland districts.

### 8.5 What We Are Not Building

To prevent scope creep, the following are explicitly out of scope for the initial release:

- Yield prediction
- Pest or disease detection
- Field-level (sub-district) analytics
- Forecasting (next week, next month projections)
- Push notifications, alerts, or subscriptions
- User accounts or saved searches
- Multi-country support
- Mobile apps (the web app is mobile-responsive, but no native iOS/Android)

Any of these may move into Future Expansion (Section 14) after the initial release.

---

## 9. Build Phases

Phase A (scaffolding) is complete. The remaining phases follow.

### Phase B — Earth Engine Authentication (~2 hours)

Goal: Earth Engine works both locally and in production.

Steps:
1. Run `earthengine authenticate` locally; verify `ee.Initialize(project='earth-engine-project')` succeeds in a Python script.
2. In Google Cloud Console, create a service account named `streamlit-runner`.
3. Grant the service account the "Earth Engine Resource Viewer" role.
4. Create and download a JSON key for the service account.
5. In Earth Engine's Cloud Console, register the service account email under the project's authorized accounts.
6. Add the JSON contents to Streamlit Cloud's app secrets under the key `gcp_service_account`.
7. Implement `atlas/ee_client.py` with an `init_ee()` function that uses service account credentials when running on Streamlit Cloud and falls back to local OAuth otherwise.
8. Add a small test to `app.py`: print `ee.Number(42).getInfo()` and verify it returns 42 on the live deployment.

### Phase C — First Indicator: NDVI (~1 day)

Goal: One climate indicator working end-to-end with the live app.

Steps:
1. Download GADM Bangladesh admin level 2 boundaries to `data/gadm_bd_admin2.geojson`.
2. Implement `atlas/districts.py` to load the GeoJSON and provide a list of district names plus an Earth Engine geometry getter.
3. Open `notebooks/01_ndvi_sandbox.ipynb` and pull NDVI for Rangpur for the past 24 months. Validate the curve against the agricultural calendar of Bangladesh (rises June–October, falls November–May).
4. Refactor the working notebook code into `atlas/ndvi.py` with a single function: `ndvi_timeseries(district_code: str, months: int = 24) -> pd.DataFrame`.
5. Update `app.py` to add a district selector and an NDVI line chart panel. The chart shows the time series with the current value annotated.
6. Add `@st.cache_data(ttl=3600)` to the NDVI function. Test that switching back to a previously selected district loads instantly.
7. Commit, push, verify on the live URL.

### Phase D — Flood Layer (~1 day)

Goal: Sentinel-1 SAR flood detection visible as a map layer.

Steps:
1. Open `notebooks/02_flood_sandbox.ipynb`. Pull Sentinel-1 GRD imagery for one district during a known flood event (the 2024 Sylhet floods is a good benchmark).
2. Implement the flood detection algorithm step by step in the notebook, testing each step against the visual map.
3. Compare a pre-flood and post-flood image; verify that flood pixels appear where expected.
4. Refactor into `atlas/flood.py`: a function that returns an Earth Engine Map ID URL plus summary statistics (flooded area in hectares).
5. Add `atlas/maps.py` helpers for folium rendering of Earth Engine Map ID layers.
6. Update `app.py` to add a flood panel below the NDVI panel. The panel shows a folium map of the district with the flood layer overlaid.
7. Commit, push, verify.

### Phase E — Moisture and Drought Composite (~0.5 day)

Goal: NDMI panel and combined drought score.

Steps:
1. Open `notebooks/03_moisture_sandbox.ipynb`. NDMI computation is structurally similar to NDVI; reuse the cloud-masking and compositing logic.
2. Implement `atlas/moisture.py` with `ndmi_timeseries(district_code, months)` and `drought_score(district_code)`.
3. Update `app.py` with a third panel showing NDMI alongside NDVI on the same chart, plus a drought score badge.
4. Commit, push, verify.

### Phase F — Coastal Salinity Proxy (~0.5 day)

Goal: Salinity panel for coastal districts.

Steps:
1. Open `notebooks/04_salinity_sandbox.ipynb`. Implement the salinity index from Sarkar et al. 2023.
2. Build `data/coastal_districts.json` with the list of 19 coastal district codes.
3. Implement `atlas/salinity.py` with `salinity_index(district_code)` returning a current value and seasonal context.
4. Update `app.py` to conditionally render the salinity panel only when a coastal district is selected. For inland districts, hide the panel cleanly.
5. Commit, push, verify.

### Phase G — Polish, Bilingual UI, Methodology Page (~1 day)

Goal: Production-ready polish.

Steps:
1. Implement `atlas/i18n.py` with English and Bangla string dictionaries. Wire all UI strings through `t(key, lang)`.
2. Add a language toggle to the sidebar.
3. Verify Bangla rendering across all components (Streamlit native widgets render UTF-8 cleanly; folium and Plotly may need font fallbacks).
4. Build the Methodology page: a Streamlit multipage view at `pages/methodology.py` with citations and limitations for each indicator.
5. Build the About page: a brief project narrative with links to source code and the underlying data.
6. Add export buttons to each panel (PNG of the map, CSV of the time series).
7. Mobile viewport testing; adjust column ratios as needed.
8. Final pass on `README.md` and `docs/`.
9. Commit, push, verify.

### Phase H — YC Application Submission (~0.5 day)

Goal: Submit the Y Combinator Startup School 2026 application with the project as a portfolio item.

Steps:
1. Save a representative Claude Code session transcript from one of the Phase B–G build sessions for the application's required upload.
2. Update LinkedIn, GitHub profile, and personal site (if applicable) with the live URL and repo link.
3. Submit the application.

### Total Estimated Time: 6 to 7 working days from end of Phase A to end of Phase H.

---

## 10. Role of Claude Code

Claude Code is the development pair-programmer. It is not the developer.

### 10.1 What Claude Code Should Do

- Generate first drafts of well-scoped functions ("write a function with this signature that does this specific thing")
- Translate working notebook code into clean module functions with docstrings and type hints
- Debug Earth Engine errors by reading the code, running it, and proposing fixes
- Write boilerplate (i18n dictionaries, requirements.txt entries, .gitignore patterns)
- Draft commit messages and pull request descriptions
- Suggest test cases for tricky logic (cloud masking edge cases, threshold sensitivity)

### 10.2 What Claude Code Should Not Do (Without Verification)

- Invent Earth Engine API methods that do not exist (this happens; always verify against `developers.google.com/earth-engine`)
- Suggest alternative web frameworks (Flask, FastAPI, React) when Streamlit handles the requirement adequately
- Refactor working code without a clear reason
- Write code that uses paid services (Mapbox tokens, AWS, Google Cloud Storage paid tiers)
- Make architectural changes without explicit instruction

### 10.3 Session Patterns

A productive Claude Code session looks like:

1. **Orient the agent.** First message: "We're working on the BCRA project. The architecture is in `docs/project_spec.md`. Today we're focused on Phase D (flood layer). Read the project spec and `atlas/flood.py` (currently empty) before suggesting changes."
2. **Set the next concrete sub-task.** "Implement `flood_map(district_code, year, month)` in `atlas/flood.py`. It should return a tuple of `(map_id_url, flooded_hectares)`. Use Sentinel-1 VV polarization with a -16 dB threshold. Mask permanent water using JRC GSW1_4."
3. **Run and verify.** After Claude writes the code, run it. Fix bugs. Iterate.
4. **Commit.** Once it works, commit with a clear message.

A typical day might run 4 to 6 such sessions. Save the most instructive session transcript for the YC application upload.

### 10.4 What Sessions to Save for YC

The Y Combinator Startup School application asks for an uploaded Claude Code session. The strongest sessions are not the ones where everything worked first try. They are the ones where:

- The developer encounters a non-obvious bug
- The developer and Claude Code work through it together
- The session ends with working code and an explanation of what was wrong

A session where you debug an Earth Engine projection mismatch over 12 messages and end with a clean fix is more compelling than a session where you say "build the app" and Claude writes it linearly.

---

## 11. Expected Outputs Per Phase

| Phase | Code Artifact | Live App State | Repo State |
|---|---|---|---|
| A (done) | `app.py` hello-world, scaffold | Live URL serves a title and welcome | Clean structure committed |
| B | `atlas/ee_client.py` | Live URL prints `42` from EE | Service account configured in Streamlit secrets |
| C | `atlas/districts.py`, `atlas/ndvi.py`, `notebooks/01_*.ipynb` | District selector + NDVI chart | GADM boundaries in `data/`, NDVI working live |
| D | `atlas/flood.py`, `atlas/maps.py`, `notebooks/02_*.ipynb` | Flood map panel added | Flood layer working live |
| E | `atlas/moisture.py`, `notebooks/03_*.ipynb` | NDMI on the same chart as NDVI | Drought score badge live |
| F | `atlas/salinity.py`, `notebooks/04_*.ipynb`, `data/coastal_districts.json` | Salinity panel for coastal districts only | Coastal-conditional UI live |
| G | `atlas/i18n.py`, `pages/methodology.py`, `pages/about.py`, `docs/methodology.md` | Bilingual, methodology page, exports, mobile-ready | Production-polished |
| H | YC application submitted | Live and stable | All commits clean |

---

## 12. Technical Risks and Debugging

### 12.1 Earth Engine Quota Exhaustion

**Risk:** The Community Tier of Earth Engine is generous but not unlimited. A spike in traffic could throttle the live app.

**Mitigation:**
- Aggressive use of `@st.cache_data(ttl=3600)` so each district-month combination is computed at most once per hour.
- Pre-compute the 5-year baseline as a static Parquet file in `data/`. The app reads from disk, not Earth Engine.
- Pre-compute district boundaries as GeoJSON. No Earth Engine call needed for boundary rendering.
- For the flood layer, use Earth Engine Map ID URLs (which serve tiles directly from Google's edge cache) rather than re-querying for each render.

**Detection:** Streamlit Cloud surfaces error logs. If we see `EEException: User memory limit exceeded` or `Computation timed out`, the cache is missing or the query is too heavy.

### 12.2 Cloud Cover Blocking Sentinel-2

**Risk:** During monsoon months (June–September), Sentinel-2 imagery is heavily affected by clouds. Some months may have no usable imagery for some districts.

**Mitigation:**
- Use cloud-mask aggregation on monthly composites; drop pixels with high cloud probability.
- If a month has no clean pixels, the chart shows a gap rather than a misleading value.
- The methodology page documents this honestly.
- Sentinel-1 (radar) is unaffected by clouds; the flood layer continues to work in monsoon.

### 12.3 SAR False Positives

**Risk:** The simple thresholding flood algorithm has known false positives (tarmac, wet rice paddies, calm water bodies missed by the permanent water mask).

**Mitigation:**
- The methodology page documents the false-positive cases.
- For the initial release, accept the false positives; the order of magnitude is correct even if the boundaries are approximate.
- A future phase may replace thresholding with a Random Forest classifier following the published Bangladesh-specific algorithm.

### 12.4 Streamlit Cloud Cold Starts

**Risk:** When the app has not been visited for a while, the first request takes 10 to 30 seconds. A YC reviewer clicking the link may experience this.

**Mitigation:**
- The README explicitly notes the cold-start behavior; this is universal for free hosting tiers and not a red flag.
- The first page should render quickly even on a cold start (no Earth Engine call until the user picks a district).
- Optionally: add a simple cron-style ping (e.g., from a free uptime-monitoring service) that hits the app every 6 hours to keep it warm during the YC review period.

### 12.5 Service Account Key Leak

**Risk:** Accidentally committing the service account JSON to the public repo would compromise the Earth Engine project.

**Mitigation:**
- The `.gitignore` includes `.streamlit/secrets.toml` and `*.json`.
- Pre-commit: visually verify `git status` before every push during the build week.
- If a leak occurs: immediately rotate the key in Google Cloud Console (delete the leaked key, create a new one, update Streamlit secrets). Do not waste time trying to scrub Git history; the key must be considered compromised the moment it is on GitHub.

### 12.6 Bangla Rendering

**Risk:** Bangla text may not render correctly in some chart libraries due to font availability.

**Mitigation:**
- Streamlit native widgets handle UTF-8 cleanly.
- For Plotly charts, specify a font that supports Bangla (e.g., `Noto Sans Bengali`).
- For folium maps, district labels can fall back to Latin transliteration if needed.
- Test on multiple browsers (Chrome, Firefox, Safari, Mobile Safari).

### 12.7 Debugging Strategy

When something breaks, in order of likelihood:

1. **Check the Streamlit Cloud logs** (Manage app → Logs). The error trace usually points to the file and line.
2. **Reproduce locally.** If it works locally but fails on Cloud, the cause is environmental: a missing dependency in `requirements.txt`, a Python version mismatch, or a missing secret.
3. **Bisect with Git.** If a recent commit broke it, `git log --oneline` and identify the suspect commit.
4. **Earth Engine specific:** Add `print(repr(ee_object))` and `print(ee_object.getInfo())` to inspect intermediate values. Earth Engine errors often appear far from the actual bug due to lazy evaluation.

---

## 13. Deployment Plan

### 13.1 Current State

- Repo: `github.com/mushfiqmahim/bcra-project` (public, main branch)
- Live URL: `bcra-project-bd.streamlit.app`
- Streamlit Cloud connected via GitHub OAuth, watches `main` branch
- Auto-deploy on every push to `main`

### 13.2 Deployment Cadence

Every push to `main` triggers a redeploy. During the build week, expect 5 to 15 deploys per day. This is normal and supported.

If a deploy fails (build error, dependency conflict), Streamlit Cloud keeps the previous version running. The user does not see the broken version. This is a major safety net.

### 13.3 Pre-Deploy Checklist

Before pushing to `main`, run locally:

```bash
streamlit run app.py
```

Click through every panel and every district. If anything breaks locally, fix it before pushing. The local environment matches the cloud environment closely enough that most issues surface locally first.

### 13.4 Post-Deploy Verification

After a push:

1. Open the Streamlit Cloud dashboard. Confirm the new build is "Live."
2. Open the live URL in an incognito window (to avoid cache).
3. Click through the changed area. Verify the change is visible.
4. If the build fails, read the logs immediately and fix.

### 13.5 Rollback

If a bad deploy reaches production:

```bash
git revert HEAD
git push
```

This creates a new commit that undoes the bad one. Streamlit Cloud redeploys with the prior state. The fix is reversible without rewriting history.

### 13.6 Backup Hosting

Streamlit Cloud is the primary host. As a backup, the app can be deployed to Hugging Face Spaces with minimal modification (Spaces also supports Streamlit apps). If Streamlit Cloud has an outage during the YC review period, this is a fallback. We do not actively maintain a backup deployment, but the option exists.

---

## 14. Future Expansion

The following are not part of the initial release but are documented for context. None of them block the YC application; all of them could be added incrementally after launch.

### 14.1 Indicator Improvements

- **Random forest flood classifier.** Replace simple SAR thresholding with the published Bangladesh-specific RF model (Thomas et al. 2019, MDPI Remote Sensing 11:1581). Reduces false positives substantially.
- **Validated salinity model.** Train a regression model against publicly available soil EC samples from coastal Bangladesh, replacing the spectral proxy with a calibrated estimate.
- **Crop type classification.** Use a public crop-type dataset (e.g., WorldCereal or Bangladesh-specific surveys) to disaggregate NDVI by crop, providing more interpretable signals.

### 14.2 New Indicators

- **Cyclone storm-surge risk.** Combine bathymetry, elevation (SRTM), and historical surge tracks into a coastal exposure score.
- **River-bank erosion.** Time-series analysis of riverbank positions from Sentinel-2, particularly for char regions.
- **Heat stress.** ECMWF ERA5 reanalysis temperature data integrated into a heat-stress index for human and crop exposure.

### 14.3 Functional Features

- **Time slider.** Let users pick any month from 2017 onward to see historical conditions, not just the most recent.
- **Compare districts.** A comparison view showing two or three districts side-by-side.
- **Downloadable reports.** A PDF generator that produces a one-page district summary with all four indicators.
- **API access.** A simple REST endpoint that returns the same data as JSON, enabling third-party integration.
- **Mobile app.** A React Native or Flutter wrapper around the same data, optimized for field use by extension officers.

### 14.4 Geographic Expansion

The architecture is country-agnostic. Adding a new country (Bhutan, Nepal, Myanmar) requires changing the boundary dataset, the coastal district list, and a few district-name conventions. The four indicators all generalize. The bilingual layer would need additional translations.

### 14.5 Research Direction

If the project sustains beyond the YC application, it could become the basis for a small open research output: a methods paper on integrating multiple remote-sensing indicators for civic transparency in low-income countries. This is well outside the scope of the initial release but is a natural direction.

---

## 15. Glossary

- **Backscatter.** The radar signal that bounces back from the Earth's surface to the SAR satellite. Smoother surfaces (water) produce less backscatter.
- **Composite.** A single image derived by combining multiple satellite passes over the same area, typically to reduce cloud cover or noise. Example: a monthly mean composite averages all clean pixels from a month.
- **dB (decibel).** Logarithmic unit used to express SAR backscatter. Open water is typically below -16 dB; vegetation is typically above -10 dB.
- **Earth Engine (GEE).** Google's planetary-scale geospatial analysis platform. Free for non-commercial use. The backbone of this project.
- **FAO GAUL.** Global Administrative Unit Layers, a free worldwide dataset of administrative boundaries maintained by the FAO and hosted on Earth Engine.
- **GADM.** A separate global administrative boundary dataset, hosted at gadm.org. We use it for client-side rendering because its files are smaller than GAUL's.
- **GeoJSON.** A standard text format for geographic features. Human-readable; parseable by every major mapping library.
- **JRC GSW.** Joint Research Centre Global Surface Water dataset; a global map of permanent and seasonal water bodies. Used to mask out non-flood water.
- **NDMI.** Normalized Difference Moisture Index; a vegetation water content index from Sentinel-2 NIR and SWIR bands.
- **NDVI.** Normalized Difference Vegetation Index; a vegetation greenness index from Sentinel-2 NIR and red bands.
- **QA60.** Quality Assurance band 60 in Sentinel-2 imagery; encodes cloud and cirrus probability per pixel.
- **SAR.** Synthetic Aperture Radar. Active sensor that emits microwave pulses and measures the return; works through clouds, day or night.
- **Sentinel-1.** ESA satellite carrying a C-band SAR sensor.
- **Sentinel-2.** ESA satellite carrying a multispectral optical sensor.
- **Service account.** A non-human Google Cloud identity used by automated systems to access Google services. Used here for Streamlit Cloud's Earth Engine access.
- **Streamlit.** A Python library that turns Python scripts into web applications.
- **VV polarization.** SAR signal that is transmitted vertically and received vertically. The most useful polarization for water detection.
- **Zonal statistics.** Aggregating raster pixel values within a polygon. Example: mean NDVI inside a district polygon.

---

*End of specification. This document is a living artifact; update it as architectural decisions evolve.*