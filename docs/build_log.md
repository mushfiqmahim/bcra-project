# BCRA — Build Log

**Purpose:** Chronological record of work completed, problems encountered, and decisions made. Captures the diagnostic and debugging history of the project so that recurring issues are not rediscovered.

This is a development log, not user-facing documentation. New phases append below.

---

## Phase A — Local Environment and Repository Setup

**Goal:** Establish a working development environment and a deployed hello-world Streamlit application before writing any project-specific code.

### Steps Completed

1. Installed Python 3.11 from python.org with `Add to PATH` enabled.
2. Installed VS Code, configured Python and Pylance extensions.
3. Installed Git for Windows; configured global identity with `git config --global user.name` and `--global user.email` using the Berea College email.
4. Installed Node.js 24.15.0 and npm 11.12.1.
5. Resolved a PowerShell execution policy block (`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`) so npm could run.
6. Installed Claude Code globally via `npm install -g @anthropic-ai/claude-code` and authenticated.
7. Created a public GitHub repository `mushfiqmahim/bcra-project` initialized with README, MIT LICENSE, and Python `.gitignore`.
8. Cloned the repo to `C:\Users\mahimm\Downloads\BCRA`.
9. Wrote a hello-world `app.py` (title plus name input). Installed Streamlit. Verified locally with `streamlit run app.py`.
10. Pushed `app.py` to GitHub. Created a Streamlit Community Cloud account using GitHub OAuth. Connected the app and deployed.
11. Confirmed the live URL `bcra-project-bd.streamlit.app` rendered the hello-world page.

### Decisions

- **Repository name `bcra-project`** chosen over longer names; matches the working directory name and is short enough for URLs.
- **Public visibility** chosen because Streamlit Community Cloud's free tier requires public repos, and the project is intended as a portfolio piece.
- **Project root inside `Downloads/`** is unconventional but is where the developer naturally placed it; not worth moving.

### Outcome

Phase A milestone reached: a Python file edited locally → committed to GitHub → automatically deployed to a public URL. This is the highest-friction part of any web project. Subsequent phases ride on this foundation.

---

## Phase B — Earth Engine Authentication

**Goal:** Earth Engine works from the local Python environment.

### Steps Completed

1. Visited `earthengine.google.com` and registered a non-commercial project. Project ID: `earth-engine-project-495404`. Selected academic / educational use, with Berea College affiliation. Approval was immediate.
2. Installed the Earth Engine Python client: `pip install earthengine-api`.
3. Ran `earthengine authenticate` from the terminal. Browser opened, authorization granted, credentials cached at `~/.config/earthengine/credentials`.
4. Wrote `test_ee.py` with a one-line check: `ee.Initialize(project="earth-engine-project-495404"); print(ee.Number(10).add(5).getInfo())`. Verified output `15`.
5. Created the `atlas/` Python package with `__init__.py` and an initial `ee_client.py` containing a single `init_ee()` wrapper. The intent: any future module can call `init_ee()` without duplicating the project ID.

### Decisions

- **Defer service account setup until Phase C wiring time.** OAuth is sufficient for local notebook work; the service account is only needed when Earth Engine must run inside a Streamlit Cloud container.
- **Use the same email for Berea registration and EE registration** to simplify the academic eligibility check.

### Outcome

`python test_ee.py` returns `15`. Earth Engine is reachable from the local Python environment.

---

## Phase C — NDVI Indicator (Sentinel-2)

**Goal:** A working NDVI time-series panel in production at `bcra-project-bd.streamlit.app`.

### C.1 Notebook Sandbox

Reference: `notebooks/01_ndvi_sandbox.ipynb`

Steps completed:

1. Created the notebook with the Jupyter extension in VS Code.
2. Installed packages into the notebook kernel: `earthengine-api`, `pandas`, `plotly`, `nbformat` (for inline rendering).
3. Initialized Earth Engine inside the notebook (same project ID).
4. Loaded Bangladesh districts from `FAO/GAUL/2015/level2`, filtered to `ADM0_NAME == 'Bangladesh'`. Confirmed 64 districts. Selected Rangpur as the test district. Verified area (~2,314 km²) and centroid (89.24E, 25.64N).
5. Filtered Sentinel-2 SR Harmonized to Rangpur over the past 24 months with `CLOUDY_PIXEL_PERCENTAGE < 60`. Got 199 raw scenes.
6. Wrote a QA60 cloud mask (bits 10 and 11) and applied to all scenes. Divided by 10000 to convert to physical reflectance.
7. Computed NDVI using `normalizedDifference(['B8', 'B4'])` per scene.
8. Built monthly composites and reduced over Rangpur with `Reducer.mean()` at scale 100m.
9. Pulled results client-side, framed as pandas DataFrame, plotted with Plotly.

### C.1 Issues Encountered

**Empty-month handling:** The first attempt at monthly aggregation failed with `EEException: Dictionary.get: Dictionary does not contain key: 'NDVI'`. Cause: when a month had zero scenes passing the cloud filter, `.mean()` on the empty collection produced an image with no bands. `reduceRegion` returned an empty dict, and `.get("NDVI")` failed.

Fix: wrap the reduction in `ee.Algorithms.If(monthly_collection.size().gt(0), <reduce>, None)` so empty months propagate as null.

**Null serialization:** After fixing empty-month handling, a `KeyError: 'ndvi'` appeared on the client. Cause: `getInfo()` strips null values from feature properties during JSON serialization, so empty months arrived without an `ndvi` key.

Fix: use `f["properties"].get("ndvi")` with a default of None instead of bracket access.

**Plotly notebook rendering:** `fig.show()` failed with `Mime type rendering requires nbformat>=4.2.0 but it is not installed`.

Fix: `%pip install nbformat` in a notebook cell.

### C.1 Validation

Rangpur 24-month NDVI matched the expected agricultural calendar:
- Aman rice canopy peaks: Sep 2024 (0.62), Oct 2025 (0.67)
- Boro rice secondary peak: Mar-May 2025 (0.52-0.55)
- Pre-monsoon trough: Jun 2024 (0.29)
- Post-Aman fallow: Dec 2024, Dec 2025 (0.35-0.36)

### C.2 Generalization Test

Re-ran the same pipeline on Khulna. Curve was structurally distinct (flatter, longer post-monsoon plateau, deep July 2025 trough at 0.21) but coherent — the differences match Khulna's coastal mangrove and aquaculture profile. Validation confirmed the function generalizes; logic is not Rangpur-specific.

### C.3 Production Refactor

Used Claude Code with a tightly scoped prompt to refactor the working notebook logic into `atlas/ndvi.py`. Key changes from notebook to production:

- Single function `ndvi_timeseries(district_name, months, end_date)` returning a DataFrame.
- Stacked-band reduction: build N monthly bands named `ndvi_YYYY_MM`, `cat()` into one image, reduce once. This is the fix for the EE concurrency limit (see issue below) and is the canonical pattern for time-series workloads.
- Empty-month branch uses `ee.Algorithms.If` with a fully-masked constant image, so the band exists but the reduction returns null.

Wrote `scripts/verify_ndvi.py` as a smoke test: runs `ndvi_timeseries` for Rangpur and Khulna with 12 months, asserts at least 9 of 12 non-null months in each. Passed on first run, with values matching the notebook output to 4+ decimal places where months overlapped.

### C.3 Issues Encountered

**Earth Engine concurrency limit (429):** When running the original notebook approach (FeatureCollection of 24 monthly Features each containing a deferred reduceRegion) on Khulna immediately after a successful Rangpur run, EE returned `HttpError 429: Too many concurrent aggregations`.

Cause: EE's Community Tier caps concurrent aggregations per user. The original FeatureCollection approach fans out all 24 reductions in parallel server-side.

Initial fix: serialize the per-month reductions client-side with a Python loop and one `getInfo` per month. This worked but was slow (40-60 seconds for 24 months) and fragile under load.

Production fix: stacked-band image with one `reduceRegion` call. One round-trip total.

### C.4 Live Wiring

Refactored `app.py` to:

- Initialize EE with `init_ee()` from `atlas.ee_client`.
- Cache the district list with `@st.cache_data(ttl=24*3600)`.
- Cache per-district NDVI with `@st.cache_data(ttl=3600)`.
- Render a district selectbox defaulted to Khulna (matches the validation case).
- Show a Plotly line chart with the latest non-null value annotated in red.

### C.4 Issues Encountered

**Empty `requirements.txt` blocks Cloud build:** First push of the new `app.py` deployed to Cloud, but the build succeeded with only Streamlit installed (auto-detected). On script execution, `import ee` failed with `ModuleNotFoundError: No module named 'ee'`.

Cause: Streamlit Cloud auto-detects bare `import streamlit` but does not extend that to `earthengine-api`, `pandas`, or `plotly`.

Fix: populate `requirements.txt` with explicit lower-bound pins for all four packages.

**Service account auth required for Cloud:** Local OAuth tokens cached in the developer's home directory are not present in a Streamlit Cloud container. The first attempt to use the deployed app resulted in EE initialization failures.

Fix: implemented dual-mode `init_ee()`:
- If `st.secrets["gcp_service_account"]` exists, construct `ee.ServiceAccountCredentials` and initialize with them.
- Otherwise fall through to bare `ee.Initialize(project=...)` for local OAuth use.
- Lazy-import `streamlit` inside a try/except so non-Streamlit callers (like the smoke test) work.

### C.5 Service Account Setup

1. Created `streamlit-runner` service account in the GCP IAM console with role `Earth Engine Resource Viewer` and downloaded JSON key.
2. Stored JSON outside the repo: `C:\Users\mahimm\OneDrive - Berea College\Documents\bcra-secrets\`.
3. First test of service-account auth (`ee.ServiceAccountCredentials(...).Initialize(...)`) failed with `HttpError 403: Caller does not have required permission to use project ... Grant the caller the roles/serviceusage.serviceUsageConsumer role`.
4. Granted `Service Usage Consumer` as a second role in the same IAM panel. Test passed: `ee.Number(7).add(8).getInfo()` returned 15.
5. Generated TOML for Streamlit Cloud secrets via:
   ```cmd
   python -c "import json; p = r'<path>'; d = json.load(open(p)); lines = ['[gcp_service_account]'] + [f'{k} = {json.dumps(v)}' for k, v in d.items()]; print('\n'.join(lines))" | Set-Clipboard
   ```
6. Pasted TOML into Streamlit Cloud's Secrets UI under app settings.
7. Re-ran `python scripts/verify_ndvi.py` to confirm the dual-mode `init_ee()` still worked locally (OAuth fallback). Passed.
8. Pushed the Cloud-mode changes. Streamlit Cloud rebuilt; the live app's NDVI panel rendered successfully for Khulna and Rangpur.

### C.5 Security Incident

During the TOML conversion step, a Python command was run that printed the full service account JSON (including private key) to the terminal and was subsequently pasted into the development chat. The key was treated as compromised and rotated:

1. Existing key revoked via GCP service accounts UI.
2. New JSON key created.
3. Old JSON file deleted from the local secrets directory.
4. New TOML generated and pasted into Streamlit Cloud's secrets store, replacing the previous block.
5. Local smoke test re-verified.

Lesson: never pipe a secret to terminal output. Use `... | Set-Clipboard` (PowerShell) or equivalent so the secret never appears on screen.

### C.6 Outcome

`bcra-project-bd.streamlit.app` shows the title, district selector, and Plotly line chart for any of 64 districts. Latest values are annotated. Caching produces instant repeat-district loads. Phase C is shipped.

---

## Phase D — Sentinel-1 SAR Flood Detection

**Goal:** A working flood-extent panel for the 2024 Sylhet event (validation case) and any other district. Currently: notebook validated, refactor pending.

### D.1 Notebook Sandbox

Reference: `notebooks/02_flood_sandbox.ipynb`

Steps completed:

1. Created the notebook in `notebooks/`. Installed `folium` (0.20.0).
2. Defined the Sylhet 2024 flood event: pre-flood window May 1-20, 2024; flood window May 25 - June 30, 2024.
3. Filtered Sentinel-1 GRD to Sylhet for both windows with `instrumentMode == 'IW'` and polarization `VV`. Got 3 pre-flood and 6 flood-window scenes total.
4. Inspected orbit passes: both ASCENDING and DESCENDING present. Selected DESCENDING per published Bangladesh flood literature; this gave 2 pre-flood and 3 flood-window scenes.
5. Built median composites of the VV band for both windows; clipped to Sylhet geometry.
6. Applied threshold of -16 dB. Pixels below threshold = water.
7. Computed area:
   - Pre-flood: 193.5 km²
   - Flood-period: 1448.6 km²
   - Multiplier: 7.5x

The pre-flood and flood numbers include permanent water bodies (rivers, haor core); we needed to exclude permanent water for the honest "flood-only" extent.

### D.2 Permanent Water Masking — The Diagnostic

This was the most technically challenging issue in the project to date.

**Initial approach:** load `JRC/GSW1_4/GlobalSurfaceWater`, threshold `occurrence > 50` to define permanent water, mask it out via `flood_water.And(permanent_water.Not())`.

Result: flood-only area returned as 314.1 km². Sanity check (`flood_area - intersection_area = 1448.6 - 99.6 = 1349.0`) showed the expected answer should be ~1,349 km². The actual answer was ~75% smaller than the bound.

**Iteration 1:** Replaced `.And()` with multiplication: `flood_water.multiply(permanent_water.Not())`. Same result: 314.1 km². The issue was not the boolean operator.

**Iteration 2:** Replaced `permanent_water.Not()` with `ee.Image(1).subtract(permanent_water)`, reasoning that `.Not()` collapses fractional resampled values to 0 while subtraction preserves them. Same result: 314.1 km². The issue was not the not-construction either.

**Iteration 3:** Replaced the formulation with `flood_water.subtract(intersection)` where `intersection = flood_water.multiply(permanent_water)`. Same result: 314.1 km². The issue was not the algebraic form.

**Iteration 4 — diagnostic cell:** Computed flood-only via four methods in parallel:
1. `flood_water.subtract(intersection)` → 314.1
2. `flood_water.where(permanent_water.eq(1), 0)` → 1301.5
3. `flood_water.updateMask(permanent_water.eq(0))` → 1301.5
4. With explicit reprojection, then subtract → 314.1

The breakthrough: methods 2 and 3 produced the expected answer (~1,300 km²); methods 1 and 4 produced the wrong one (~314 km²). The common factor in failing methods was `subtract` between flood_water and a derived multiplication.

**Root cause:** Sentinel-1 native projection is 10m UTM; JRC GSW native is 30m EPSG:4326. EE operations that mix these two projections trigger internal resampling, producing fractional values at the boundaries of binary regions. Fractional values flow correctly through multiplication (a 0.7 × 1 contributes 0.7 to area sums) but flow incorrectly through `subtract` followed by area summation when the operation is logically equivalent to a binary AND/AND-NOT.

**Fix:** use `updateMask(permanent_water.eq(0))` for the boolean exclusion. This routes through EE's evaluation graph differently and avoids the resampling artifact.

### D.2 Validation Results

After applying the `updateMask` fix:

- Permanent water in Sylhet: 102.9 km²
- Flood total: 1448.6 km²
- Flood AND permanent (overlap): 99.6 km²
- Flood-only extent: 1301.5 km²
- Share of district: 37.4%

This matches published reporting on the 2024 Sylhet event (60-80% of Sylhet *division* submerged at peak; Sylhet *district* alone 30-40% at the median across the flood window).

### D.3 Visualization

Rendered the flood-only mask as a folium TileLayer over an OpenStreetMap basemap, with permanent water in blue and flood-only in red. The flood pattern visually concentrates in the haor basin (lower-elevation central and southern Sylhet) and avoids the higher eastern hills, consistent with topographic expectation.

VS Code initially blocked inline map rendering ("Make this Notebook Trusted to load map"). Resolved by saving the map to `flood_map_sylhet.html` and opening in a browser. Added `*.html` to `.gitignore` so saved maps don't pollute the repo.

### D.4 False-Positive Control

Re-ran the same pipeline on the same district (Sylhet) for a known dry-season window (Feb 1-20 pre, Feb 25 - Mar 31 target). Result:
- Pre water: 127.9 km²
- Target water: 75.1 km²
- Flood-only: 27.9 km²
- Share of district: 0.8%

A 0.8% false-positive rate during a confirmed dry period, vs 37.4% during the documented flood, is a 47x contrast. The methodology distinguishes flood from baseline cleanly.

### D.5 Outcome

The notebook is committed and pushed. Phase D's notebook portion is complete. Refactor into `atlas/flood.py` and live wiring are pending; instructions are in `session_handoff.md` Section 5.

---

## Decisions Log

Cross-referenced architectural decisions made during the project, with their rationale.

1. **Streamlit over a custom web framework.** Single-developer velocity; data-app focus; no JS required.
2. **Earth Engine over local geospatial.** Imagery is too large for local processing on a free hosting tier.
3. **GitHub + Streamlit Community Cloud over self-hosted.** Free, automatic, low maintenance.
4. **Service account over OAuth in production.** Required for headless Cloud deployment.
5. **Dual-mode `init_ee()`.** Single codebase works on both developer machine (OAuth) and production (service account).
6. **Stacked-band reduction over per-feature reductions.** Avoids EE concurrency limit; one round-trip instead of N.
7. **Median compositing over mean for SAR.** Speckle resilience.
8. **DESCENDING orbit pass for Bangladesh flood mapping.** Per published literature (Thomas et al. 2019).
9. **`updateMask` over `.Not()` or `subtract` for permanent water masking.** Documented above; the only formulation that avoids projection-resampling artifacts.
10. **Lower-bound version pins (`>=`) over exact pins.** Reduces lockfile maintenance for a single-developer project.
11. **Public GitHub repo.** Required by Streamlit Cloud free tier; aligned with portfolio goal.
12. **Lower-than-permanent JRC threshold (50% occurrence).** Excludes water-half-the-time pixels from permanent classification, but the dry-season control test confirms the contribution is small (0.8% of district).

---

*End of build log. New phases append below.*
