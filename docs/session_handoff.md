# BCRA — Session Handoff

**Purpose:** Brief a new engineering session on the exact current state of the project and the next concrete actions. This document is operational, not architectural; for system design see `project_spec.md`.

**Last updated:** Post-Phase G hot-fixes complete — IAM unblocked `getMapId`, folium's bare-GeoJSON `iter_coords` crash replaced with a custom bounds extractor (now also handling `GeometryCollection`), and the fallback `else` branch instruments which condition fired. Flood map renders normally in production; defensive paths and diagnostic logging remain as safety nets.

---

## 1. Current State Summary

| Phase | Description | Status |
|-------|-------------|--------|
| A | Local environment, GitHub repo, hello-world Streamlit deploy | Complete |
| B | Earth Engine authentication (local OAuth + Cloud service account) | Complete |
| C | NDVI module, panel wiring, live deployment | Complete |
| D | Sentinel-1 SAR flood detection | Complete |
| E | NDMI / drought composite | Complete |
| F | Coastal salinity proxy | Complete |
| G | Bilingual UI, methodology page, exports, polish | Complete |
| H | YC Startup School 2026 application submission | Not started |

The live application at `bcra-project-bd.streamlit.app` currently shows:
- Title and caption
- District selectbox (defaults to Khulna; 64 districts available)
- NDVI line chart for the selected district, 24-month window
- Latest non-null NDVI value annotated in red
- NDMI line chart for the selected district, 24-month window (blue line, y-range [-0.5, 0.7]) with latest non-null value annotated
- Flood extent panel — three metrics (flood-only, permanent water, flood total in km²) and a folium map with red flood pixels over the district outline, fixed to the 2024 monsoon window (May 25 – Jun 30)
- Coastal salinity panel — two metrics (dry-season SI Mar–May, monsoon-season SI Jul–Sep) for the 2024 calendar year, gated to the 19 coastal districts; inland districts see an explanatory caption
- Sidebar navigation to a separate Methodology page documenting formulas, data sources, interpretation, and limitations for all four indicators (rendered LaTeX, references included)
- "Download CSV" button below each indicator panel (NDVI, NDMI, flood, salinity); salinity button gated to coastal districts. Filenames follow `bcra_<indicator>_<slug>_<window>.csv` with apostrophes stripped and whitespace replaced by underscore.
- Sidebar "Language / ভাষা" radio with English (default) and বাংলা options on every page; selection persists across pages via `st.session_state["language"]`. All 98 keys have populated Bangla values; technical acronyms (NDVI, NDMI, SAR, B-band identifiers, dataset IDs) and citations stay verbatim per academic-Bangla convention.
- Earth-green Streamlit theme via `.streamlit/config.toml` (primaryColor `#3D6B47`); shared sidebar chrome (project name + tagline + language radio + GitHub link) and three-piece page footer (project name · GitHub · Methodology) rendered consistently on both pages.
- Horizontal-rule dividers between consecutive indicator panels for consistent visual rhythm across NDVI, NDMI, flood, and salinity sections.

## 2. What Is Working

### 2.1 In Production (Cloud)

- Service account authentication against Earth Engine
- Per-district NDVI fetch and rendering
- Per-district NDMI fetch and rendering
- Per-district flood extent fetch and folium map rendering
- Per-district seasonal salinity (Bouaziz SI) fetch and metric rendering for coastal districts
- Multi-page Streamlit app: indicators on the home page, methodology on a dedicated `pages/methodology.py` page (no Earth Engine compute on that page)
- Per-panel CSV download buttons; serialization is pure-pandas with no extra Earth Engine round-trips (the cached panel data is reused)
- i18n via `atlas/i18n.py` and `data/strings.json` (98 keys, dot-notation, both English and Bangla populated); every user-visible string in `app.py` and `pages/methodology.py` flows through `t("key")` with English fallback and key-as-breadcrumb fallback
- Shared UI chrome via `atlas/ui.py` (`sidebar_chrome()` and `app_footer()`); both pages call the same helpers so the sidebar and footer stay in sync
- Streamlit cache (district list 24h, NDVI 1h, NDMI 1h, flood 6h, salinity 24h)
- District switching (cached districts return instantly; uncached take 20-30s)

### 2.2 Locally Verified

- `python scripts/verify_ndvi.py` — runs `ndvi_timeseries` on Rangpur and Khulna with 12-month windows; both produce DataFrames with at least 9 of 12 non-null months.
- `python scripts/verify_flood.py` — runs `flood_extent` on Sylhet over the 2024 monsoon event window (1301.5 km² flood-only) and the dry-season control window (27.9 km²); both assertions pass and reproduce notebook numbers exactly.
- `python scripts/verify_ndmi.py` — runs `ndmi_timeseries` on Rangpur and Khulna with 12-month windows; both produce ≥9/12 non-null months with all values within the [-0.5, 0.7] sanity range.
- `python scripts/verify_salinity.py` — runs `salinity_seasonal` for all 19 coastal districts in 2024; gating tests pass (Khulna coastal, Rangpur not, ValueError raised for non-coastal); all 19 districts resolve in FAO GAUL with both seasonal SI values inside [0, 0.3].
- `python scripts/verify_exports.py` — pure-pandas test (no Earth Engine) for `atlas/exports.py`; covers slug rules, header column order for NDVI/NDMI, NaN/None roundtrip behavior, and single-row shapes for salinity (4 cols) and flood (6 cols).
- `python scripts/verify_i18n.py` — standalone test (no Earth Engine, no Streamlit runtime) for `atlas/i18n.py` and `data/strings.json`; checks structural integrity of all 95 entries, non-empty English values, null-or-non-empty Bangla, smoke lookup, and missing-key fallback.
- `streamlit run app.py` — renders the production UI locally using OAuth credentials.
- Sentinel-1 SAR flood pipeline in `notebooks/02_flood_sandbox.ipynb` — produces correct flood extent for Sylhet 2024 (1301.5 km², 37.4% of district), confirmed against published reporting.
- Dry-season control test in the same notebook — produces 27.9 km² (0.8% of district), confirming low false-positive rate.

### 2.3 Repository State

Files in the repo (relevant to current work):

- `app.py` — Streamlit entry point with NDVI, NDMI, flood, and salinity panels wired in; `page_title` set to "BCRA — Indicators"
- `pages/methodology.py` — pure-content methodology page (no EE compute); rendered LaTeX for all four spectral formulas, `st.warning` callout above the salinity section, references list at bottom
- `atlas/__init__.py` — empty package marker
- `atlas/ee_client.py` — dual-mode `init_ee()`
- `atlas/ndvi.py` — production NDVI module with stacked-band reduction
- `atlas/moisture.py` — production NDMI module (Sentinel-2 B8/B11, structurally parallel to `ndvi.py`)
- `atlas/flood.py` — production flood module (Sentinel-1 VV median composite, JRC permanent-water `updateMask`)
- `atlas/salinity.py` — production salinity module (Bouaziz SI = √(B2 × B4) on Sentinel-2 SR Harmonized, two seasonal bands, coastal-only)
- `atlas/exports.py` — pure-pandas CSV serializers for the four indicators plus `slugify_district` (strips apostrophes, lowercases, replaces whitespace with underscore); LF line endings forced for cross-platform consistency
- `atlas/i18n.py` — bilingual string lookup with optional Streamlit awareness; lazy-imports streamlit only when already in `sys.modules` (silent under `python script.py`); `language_selector_sidebar()` renders the bilingual radio
- `atlas/ui.py` — shared `sidebar_chrome()` and `app_footer()`; lazy streamlit imports; `GITHUB_URL` constant
- `data/strings.json` — 98 dot-notation keys spanning the indicators page, the methodology page, and shared chrome; both English and Bangla populated
- `.streamlit/config.toml` — `[theme]` block (earth-green primary, warm off-white background, sans-serif font); secrets file remains untracked via `.gitignore`
- `data/coastal_districts.json` — 19-district allow-list using FAO GAUL spellings (Barisal, Chittagong, Jessore — pre-2018 names)
- `requirements.txt` — `streamlit>=1.30`, `earthengine-api>=1.0`, `pandas>=2.2`, `plotly>=5.20`, `folium>=0.20`, `streamlit-folium>=0.20`
- `notebooks/01_ndvi_sandbox.ipynb` — NDVI sandbox with Rangpur and Khulna validation
- `notebooks/02_flood_sandbox.ipynb` — flood sandbox with Sylhet 2024 validation and dry-season control
- `scripts/verify_ndvi.py` — NDVI smoke test
- `scripts/verify_ndmi.py` — NDMI smoke test (Rangpur and Khulna, ≥9/12 non-null, values within [-0.5, 0.7])
- `scripts/verify_flood.py` — flood smoke test (Sylhet event > 1000 km², dry-season < 100 km²)
- `scripts/verify_salinity.py` — salinity smoke test (gating + 19-district FAO GAUL resolution sweep)
- `scripts/verify_exports.py` — exports smoke test (pure pandas, no Earth Engine)
- `scripts/verify_i18n.py` — i18n smoke test (no Earth Engine, no Streamlit runtime required)
- `docs/project_spec.md` — architecture document
- `.gitignore` — excludes `*.log`, `*.html` (HTML pattern was added but may be on a concatenated line; verify)
- `LICENSE` — MIT
- `README.md` — minimal placeholder

Configuration in Streamlit Cloud (not in repo):

- `gcp_service_account` TOML block under app secrets, populated from the rotated service account JSON

## 3. What Is Partially Done

- **`.gitignore` formatting.** The `*.log` and `*.html` patterns may be concatenated to the previous line. Open in VS Code and verify each pattern is on its own line.

## 4. What Is Not Started

- `atlas/maps.py` — folium helpers for rendering EE tile layers in Streamlit (the flood panel currently inlines the folium wiring in `app.py`; if a second map indicator joins, factor out)
- Phase H — YC Startup School 2026 application submission

## 5. Next Three Concrete Actions

These are the immediate next steps. Execute in order.

### Action 1: Refactor flood pipeline into `atlas/flood.py` using Claude Code — DONE

Shipped in commit `e063cd2` on `main`. `atlas/flood.py` exposes `flood_extent(...)` matching the spec; `scripts/verify_flood.py` reproduces the notebook's 1301.5 km² event and 27.9 km² dry-season control. Action 2 is the next step.

Original instructions for reference:


In the project root, run:

```cmd
cd C:\Users\mahimm\Downloads\BCRA
claude
```

Open Claude Code with this scoped prompt:

```
We are working on the BCRA project (Bangladesh Climate Risk Atlas).

Context to read first, in order:
1. docs/project_spec.md - architectural reference
2. docs/session_handoff.md - current state
3. notebooks/02_flood_sandbox.ipynb - the working flood pipeline to be refactored
4. atlas/ndvi.py - the established pattern for atlas modules

Task: refactor the working Sentinel-1 SAR flood pipeline from the
sandbox notebook into a new module atlas/flood.py.

Public API:
    def flood_extent(
        district_name: str,
        flood_start: str,           # ISO date 'YYYY-MM-DD'
        flood_end: str,
        pre_start: str | None = None,   # defaults to flood_start - 25 days
        pre_end: str | None = None,     # defaults to flood_start - 5 days
        orbit_pass: str = 'DESCENDING',
        threshold_db: float = -16,
    ) -> dict
returning a dict with keys:
    'flood_only_image': ee.Image     # the masked flood-only mask
    'flood_only_area_km2': float
    'permanent_water_area_km2': float
    'flood_total_area_km2': float
    'district_geometry': ee.Geometry # for downstream rendering

Internal implementation requirements:
1. Use updateMask(permanent_water.eq(0)) for the permanent-water removal step.
   Do NOT use .Not() or .subtract() — those produce projection artifacts.
   See docs/build_log.md section 'Phase D diagnostic' for the record.
2. Use median compositing (not mean) for SAR speckle reduction.
3. Use ee.Algorithms.If for empty pre-flood window handling.
4. Caller is responsible for init_ee(), as in atlas/ndvi.py.
5. No tutorial-style comments. Type hints on the public function only.
6. Internal helpers (_district_geometry, _vv_composite) prefixed with underscore.

Also create scripts/verify_flood.py that:
1. Calls init_ee()
2. Runs flood_extent for Sylhet over 2024-05-25 to 2024-06-30
3. Asserts flood_only_area_km2 > 1000 (the validated event was 1301.5)
4. Runs the same call for the dry-season control window 2024-02-25 to 2024-03-31
5. Asserts the dry-season flood_only_area_km2 < 100

Do not modify app.py. Do not commit. Show the files when done.
```

Verify locally with `python scripts/verify_flood.py`. Both assertions should pass. Numbers should match notebook output to within 1%.

If the smoke test passes, commit:

```cmd
git add atlas/flood.py scripts/verify_flood.py
git commit -m "Add flood detection module with stacked-image masking"
git push
```

### Action 2: Wire flood panel into `app.py` — DONE

Shipped in commit `ae7674f` on `main`. `app.py` now renders the flood panel below the NDVI chart with three `st.metric` widgets and a folium map (district outline + JRC permanent-water-masked flood overlay) for the fixed 2024-05-25 → 2024-06-30 window. `requirements.txt` gained `folium>=0.20` and `streamlit-folium>=0.20`.

Original instructions for reference:


```
Wire atlas/flood.py into app.py as a second panel below the NDVI chart.

Requirements:
1. Add folium and streamlit-folium to requirements.txt (lower bounds only).
2. Use a fixed flood-event window for the initial release: 2024-05-25 to
   2024-06-30 (the documented Sylhet event). Show this for ALL districts
   for now; per-district event windows are a Phase G concern.
3. Render the flood extent on a folium map with:
   - District geometry as a black outline
   - Flood-only pixels in red (semi-transparent)
   - OpenStreetMap basemap
   - LayerControl panel for toggling
4. Display the area numbers as a metric row above the map:
   flood_only_area_km2, permanent_water_area_km2, % of district
5. Cache the flood compute with @st.cache_data(ttl=6*3600)

Do not modify atlas/flood.py. Do not commit.
```

Test locally: `streamlit run app.py`. Confirm both panels render for Sylhet (where flood is the focal validation case) and a non-flood district (where flood-only should still render but show much less coverage).

Commit and push:

```cmd
git add app.py requirements.txt
git commit -m "Wire flood panel into app with folium map rendering"
git push
```

Watch the Streamlit Cloud rebuild; folium will install on first build (extra 30-45 seconds in the build log).

### Action 3: Verify live deployment — DONE

User confirmed in browser on 2026-05-05: Sylhet renders NDVI + flood metrics + folium map with red flood pixels over ~37% of the district outline; non-flooded districts render the panel with minimal red coverage as expected. Phase D shipped.

Original instructions for reference:


1. Open `bcra-project-bd.streamlit.app` in an incognito window.
2. Switch to Sylhet. Confirm the NDVI chart renders, then the flood map renders below it. The map should show red flood pixels covering roughly 37% of the district outline.
3. Switch to a non-coastal, non-Sylhet district (e.g., Rangpur). Confirm the flood map still renders but shows minimal flood pixels (this is correct — Rangpur was not heavily flooded in May-June 2024).
4. If both render correctly, Phase D is shipped. Update `docs/session_handoff.md` Phase D status to "Complete" and commit.

If the live build fails, the Streamlit Cloud log is the first place to look. Common failure: missing dependency for folium's transitive needs. Add to `requirements.txt`, push again.

## 6. Known Friction Points

These are issues that have already been encountered and resolved. New work should benefit from this list rather than rediscovering them.

### 6.1 Earth Engine projection artifacts

**Symptom:** A logical operation that should yield X km² of flood extent returns approximately X/4 km² instead.

**Cause:** EE operations on images with different native projections (Sentinel-1 at 10m UTM versus JRC GSW at 30m EPSG:4326) trigger internal resampling. Boolean operations like `.Not()` and arithmetic `subtract` collapse fractional resampled values incorrectly.

**Fix:** Use `updateMask(other.eq(0))` for boolean exclusion. Use multiplication for area-weighted intersection (it preserves fractional values). Use `where(condition, value)` for conditional replacement. Avoid `.Not()` chained with multiplication and avoid `subtract` between binary images derived from multi-projection sources.

### 6.2 Earth Engine concurrency limit

**Symptom:** `HttpError 429: Too many concurrent aggregations`.

**Cause:** A FeatureCollection containing N features each with a `reduceRegion` evaluates all N reductions in parallel server-side. Community Tier hits the per-user concurrency cap around 20-30 parallel reductions.

**Fix:** Stack N inputs into a single multi-band image and reduce once. This is the production NDVI pattern.

### 6.3 Streamlit Cloud Python version

**Symptom:** `runtime.txt` says `3.12` but logs show Python 3.14.4.

**Cause:** Streamlit Cloud may ignore or override `runtime.txt`. The codebase is compatible.

**Fix:** Don't depend on a specific Python version. Avoid 3.12-only features.

### 6.4 Empty `requirements.txt` blocks deploys

**Symptom:** Cloud build runs but `import ee` fails at runtime with `ModuleNotFoundError: No module named 'ee'`.

**Cause:** Streamlit Cloud auto-detects bare `import streamlit` if `requirements.txt` is empty, but does not extend that detection to other packages.

**Fix:** Always populate `requirements.txt` with explicit lower-bound pins.

### 6.5 Service account roles

**Symptom:** `HttpError 403: Caller does not have required permission to use project ... Grant the caller the roles/serviceusage.serviceUsageConsumer role`.

**Cause:** Service account has `Earth Engine Resource Viewer` but lacks `Service Usage Consumer`.

**Fix:** Grant both roles in IAM. Both are required.

### 6.6 OneDrive-synced credentials

**Symptom:** Service account JSON in `Documents/bcra-secrets/` does not appear in `Documents/`.

**Cause:** Default Documents folder is OneDrive-synced; physical path is `OneDrive - Berea College/Documents/`.

**Fix:** Use right-click → Copy as path to get the real path. The OneDrive sync itself is acceptable for this project, but the credential stored there is treated as compromised if leaked anywhere outside the intended path.

### 6.7 PowerShell command compatibility

**Symptom:** Commands like `Add-Content` and `Set-Clipboard` work in PowerShell but fail in cmd.exe with `'Add-Content' is not recognized as an internal or external command`.

**Cause:** PowerShell cmdlets are not part of cmd.exe.

**Fix:** Use cmd-compatible alternatives (`echo *.log >> .gitignore`) or open PowerShell explicitly.

### 6.8 Concatenated cmd commands

**Symptom:** `git statusgit commit -m "..."` returns `'statusgit' is not a git command`.

**Cause:** Two terminal commands pasted as one without a newline in between.

**Fix:** Run each command separately. When copying from chat, copy one line at a time.

### 6.9 Git push rejected after web-UI edit

**Symptom:** `git push` rejected with `Updates were rejected because the remote contains work that you do not have locally`.

**Cause:** A commit was made on origin (likely via GitHub web UI) that is not on the local machine.

**Fix:** `git pull --rebase origin main`, then `git push`.

### 6.10 Empty Jupyter notebook commit

**Symptom:** `git commit` on a new `.ipynb` file shows `0 insertions(+), 0 deletions(-)` and the file appears empty on GitHub.

**Cause:** VS Code holds notebook content in memory but does not always flush to disk before the file is staged.

**Fix:** Press Ctrl+S to force-save the notebook before `git add`.

### 6.11 Flood map tile generation fails on Streamlit Cloud (resolved)

**Symptom:** On the live deployment the flood panel raised `ee.ee_exception.EEException` at `result["flood_only_image"].selfMask().getMapId(...)` inside `_cached_flood`. The numerical metrics from `flood_extent` (which use `reduceRegion`) succeeded; only the tile-URL generation failed. Local OAuth was unaffected; only the Streamlit Cloud service account triggered it.

**Cause:** missing IAM permission on the service account for the Maps API endpoint that `getMapId` calls.

**Resolution:** IAM permission granted on the service account; `getMapId` now succeeds in production. The defensive `try/except` shipped in `28db4f5` stays in place as a safety net — on any future tile-generation failure the panel sets `tile_url=None`, logs the traceback via `logging.exception`, and renders an `st.info` callout (`app.flood.map_unavailable`) instead of crashing.

### 6.12 folium `get_bounds()` raises `KeyError` on bare GeoJSON geometries (resolved)

**Symptom:** Once the IAM fix unblocked `getMapId`, the flood panel started crashing one line later at `district_layer.get_bounds()` with `KeyError` inside `folium.utilities.iter_coords`. Local OAuth and production both affected; only surfaced after the IAM fix unmasked it.

**Cause:** `ee.Geometry.getInfo()` returns a bare GeoJSON geometry (`{"type": "Polygon", "coordinates": [...]}`), not a `Feature` wrapper. folium's `iter_coords` assumes a Feature shape and dereferences `geom["geometry"]["coordinates"]`, which fails on the bare object.

**Resolution:** Replaced the folium-driven bounds computation with a custom `_bounds_from_geojson(geom)` helper that walks the raw `coordinates` list directly and returns `[[min_lat, min_lon], [max_lat, max_lon]]`. Handles bare geometries, `Feature` wrappers, and `GeometryCollection` (recursive merge of sub-geometry bounds); returns `None` on malformed input, in which case the panel falls into the same `st.info` fallback branch as the prior tile-failure case. `district_layer.get_bounds()` is no longer called anywhere. The fallback `else` branch logs which condition fired (`tile_url is None` vs `bounds=None`, with the actual geojson `type`) so future regressions are diagnosable without code changes. See commits `6df76a7` and `1e99a6a`.

## 7. Environment Details

### 7.1 Developer Machine

- **OS:** Windows 11
- **Project root:** `C:\Users\mahimm\Downloads\BCRA`
- **Python:** 3.11 (system install at `C:\Users\mahimm\AppData\Local\Programs\Python\Python311\`)
- **Editor:** VS Code with Python and Jupyter extensions
- **Shell:** cmd.exe (the project's known terminal). PowerShell is also available but commands have been written for cmd.
- **Git:** 2.54 at `C:\Users\mahimm\AppData\Local\Programs\Git\bin\git.exe`
- **Node.js:** 24.15.0
- **npm:** 11.12.1
- **Claude Code:** installed via `npm install -g @anthropic-ai/claude-code`; authenticated to Anthropic

### 7.2 Streamlit Cloud

- **Python:** 3.14.4 (chosen by Streamlit Cloud)
- **Package manager:** `uv pip install`
- **Container:** Debian-based Linux

### 7.3 Earth Engine

- **Local auth:** OAuth via `earthengine authenticate` (credentials cached in `~/.config/earthengine/credentials`)
- **Cloud auth:** Service account `streamlit-runner@earth-engine-project-495404.iam.gserviceaccount.com`
- **Service account JSON:** `C:\Users\mahimm\OneDrive - Berea College\Documents\bcra-secrets\earth-engine-project-495404-795bc480f53d.json`
- **Project ID:** `earth-engine-project-495404`
- **Quota tier:** Community (free, non-commercial)

## 8. Earth Engine Setup Status

### 8.1 Local

Confirmed working with `python -c "import ee; ee.Initialize(project='earth-engine-project-495404'); print(ee.Number(7).add(8).getInfo())"` returning 15.

### 8.2 Cloud

Confirmed working — the live app's NDVI panel successfully fetches Sentinel-2 data, which requires service-account auth.

The TOML secret block in Streamlit Cloud is structured as:

```toml
[gcp_service_account]
type = "service_account"
project_id = "earth-engine-project-495404"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "streamlit-runner@earth-engine-project-495404.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

If a key rotation is required, regenerate the JSON via `Add Key` in the GCP service accounts UI, regenerate the TOML via the helper command in `build_log.md`, and paste the result into Streamlit Cloud's secrets UI.

## 9. Key File and URL References

### 9.1 URLs

- **GitHub repo:** https://github.com/mushfiqmahim/bcra-project
- **Live app:** https://bcra-project-bd.streamlit.app
- **Streamlit Cloud dashboard:** https://share.streamlit.io
- **GCP IAM:** https://console.cloud.google.com/iam-admin/iam?project=earth-engine-project-495404
- **GCP service accounts:** https://console.cloud.google.com/iam-admin/serviceaccounts?project=earth-engine-project-495404
- **Earth Engine docs:** https://developers.google.com/earth-engine/guides

### 9.2 Critical local paths

- Project root: `C:\Users\mahimm\Downloads\BCRA`
- Service account JSON: `C:\Users\mahimm\OneDrive - Berea College\Documents\bcra-secrets\earth-engine-project-495404-795bc480f53d.json`
- Earth Engine OAuth credentials: `C:\Users\mahimm\.config\earthengine\credentials`

### 9.3 Working terminal commands

```cmd
:: Activate project
cd C:\Users\mahimm\Downloads\BCRA

:: Run app locally (uses OAuth)
streamlit run app.py

:: Smoke test NDVI module
python scripts/verify_ndvi.py

:: Open Claude Code
claude

:: Standard git flow
git status
git add <files>
git commit -m "..."
git push
```

## 10. Working Conventions

These were established during development and should be preserved.

- **Tone:** Professional, concise, no marketing language, no emojis.
- **Step-by-step pacing:** When walking through new work, move one step at a time and wait for output before continuing. Especially important for unfamiliar domains (Earth Engine, SAR, etc).
- **Authoritative diagnosis:** When code fails, identify the cause from evidence rather than guessing. The diagnostic process matters as much as the fix.
- **Commit discipline:** `git status` before every `git add`. Explicit file paths in `git add` instead of `git add .` to avoid accidentally staging secrets or junk.
- **Validation discipline:** Every new pipeline gets a happy path validation (Sylhet 2024 for flood) and a control test (dry-season for flood). Numbers must be order-of-magnitude reasonable against published external sources.
- **Documentation discipline:** When a non-obvious lesson is learned (e.g., the projection artifact issue), it goes into `build_log.md` with the diagnostic record so it isn't relearned.

---

*End of session handoff. Update Phase status table at top whenever a phase completes.*
