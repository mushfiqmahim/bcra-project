"""BCRA methodology page: formulas, data sources, interpretation, limitations."""
import streamlit as st

st.set_page_config(page_title="BCRA — Methodology", layout="wide")

st.title("Methodology")

st.markdown(
    "The Bangladesh Climate Risk Atlas (BCRA) is a free, public dashboard that "
    "exposes satellite-derived climate-risk indicators for every district of "
    "Bangladesh. All indicators are computed on Google Earth Engine and reduced "
    "to the administrative-district level (ADM2) defined by FAO GAUL 2015."
)
st.markdown(
    "This page documents the formulas, data sources, interpretation, and "
    "limitations for the four indicators currently shipped: NDVI, NDMI, flood "
    "extent, and the Bouaziz salinity proxy. The salinity indicator is a "
    "remote-sensing proxy, not a calibrated soil-salinity measurement; the "
    "limitations sections should be read as carefully as the formulas."
)

st.divider()

st.header("1. Vegetation Health (NDVI)")

st.subheader("Description")
st.markdown(
    "NDVI captures photosynthetic vegetation cover. In Bangladesh, NDVI tracks "
    "the rice agricultural calendar with two pronounced peaks — Aman rice in "
    "September–October and Boro rice in March–May — separated by post-harvest "
    "troughs."
)

st.subheader("Formula")
st.latex(r"\mathrm{NDVI} = \frac{B_{8} - B_{4}}{B_{8} + B_{4}}")
st.markdown(
    "where $B_{8}$ is Sentinel-2 NIR (842 nm) and $B_{4}$ is Sentinel-2 Red "
    "(665 nm), both in surface reflectance units."
)

st.subheader("Data Sources")
st.markdown(
    "- Sentinel-2 Level-2A from `COPERNICUS/S2_SR_HARMONIZED`, filtered to the "
    "district polygon and to scenes with `CLOUDY_PIXEL_PERCENTAGE < 60`.\n"
    "- Cloud and cirrus masking via QA60 bits 10 and 11.\n"
    "- Monthly composites built across a 24-month rolling window, reduced at "
    "100 m scale, district-level mean."
)

st.subheader("Interpretation")
st.markdown(
    "Higher NDVI indicates more vigorous green cover. Values typically range "
    "from 0.2 (bare soil, post-harvest) to 0.7 (peak canopy). The bimodal peaks "
    "align with the two rice cycles; the timing and amplitude carry information "
    "about cropping intensity and growing-season conditions."
)

st.subheader("Limitations")
st.markdown(
    "- Cloud cover during the monsoon can produce missing months. The dashboard "
    "surfaces these as gaps rather than interpolating.\n"
    "- District-level mean averages over heterogeneous land cover (cropland, "
    "settlement, water, forest) and cannot distinguish among them.\n"
    "- NDVI saturates above approximately 0.6 for dense canopies, so peak "
    "vegetation differences are compressed.\n"
    "- The Sentinel-2 record begins in 2015; longer-term baselines are not "
    "available from this sensor alone."
)

st.divider()

st.header("2. Surface Moisture (NDMI)")

st.subheader("Description")
st.markdown(
    "NDMI captures water content in vegetation canopies and surface soil. It "
    "complements NDVI: where NDVI tracks how much green is present, NDMI tracks "
    "how wet that green is."
)

st.subheader("Formula")
st.latex(r"\mathrm{NDMI} = \frac{B_{8} - B_{11}}{B_{8} + B_{11}}")
st.markdown(
    "where $B_{8}$ is NIR (842 nm) and $B_{11}$ is SWIR1 (1610 nm)."
)

st.subheader("Data Sources")
st.markdown(
    "- Identical ingestion path to NDVI: `COPERNICUS/S2_SR_HARMONIZED`, "
    "`CLOUDY_PIXEL_PERCENTAGE < 60`, QA60 mask, monthly composites at 100 m, "
    "24-month rolling window."
)

st.subheader("Interpretation")
st.markdown(
    "Higher NDMI indicates more moisture. Tracks irrigation, recent rainfall, "
    "and standing water in rice paddies. In Bangladesh, NDMI tends to peak "
    "during and just after the monsoon, with a secondary rise during Boro "
    "irrigation in the dry season."
)

st.subheader("Limitations")
st.markdown(
    "- Same cloud-cover constraint as NDVI; missing monsoon months are common.\n"
    "- Saturates over open water surfaces; does not distinguish flooded paddies "
    "from natural wetlands.\n"
    "- Conflates plant water content with soil moisture; the two cannot be "
    "separated from a district-level mean.\n"
    "- SWIR1 is at 20 m native resolution while NIR is at 10 m; both are "
    "resampled to a common scale internally by Earth Engine."
)

st.divider()

st.header("3. Flood Inundation Extent")

st.subheader("Description")
st.markdown(
    "Sentinel-1 Synthetic Aperture Radar (SAR) detects standing water by "
    "exploiting the fact that smooth water surfaces reflect radar away from "
    "the sensor, producing low backscatter values. SAR is unaffected by cloud "
    "cover, which makes it the only practical sensor for monsoon-season flood "
    "mapping in Bangladesh."
)

st.subheader("Method")
st.markdown(
    "For a given district and event window:\n\n"
    "1. Filter Sentinel-1 GRD to `instrumentMode == 'IW'`, polarization "
    "includes `'VV'`, orbit pass `'DESCENDING'` (per published Bangladesh "
    "flood literature).\n"
    "2. Take the median composite of the VV band over the event window. "
    "Median compositing reduces speckle better than mean.\n"
    "3. Apply threshold: VV < −16 dB → water. The −16 dB value is established "
    "in published Bangladesh SAR literature.\n"
    "4. Exclude permanent water using JRC Global Surface Water "
    "(occurrence > 50 %) via "
    "`flood_water.updateMask(permanent_water.eq(0))`.\n"
    "5. Compute area as `mask × pixelArea` summed within the district polygon."
)

st.subheader("Data Sources")
st.markdown(
    "- `COPERNICUS/S1_GRD` (Sentinel-1 Ground Range Detected).\n"
    "- `JRC/GSW1_4/GlobalSurfaceWater` for permanent-water exclusion.\n"
    "- `FAO/GAUL/2015/level2` for district geometry.\n"
    "- The dashboard currently displays a fixed flood-event window of "
    "25 May – 30 June 2024, corresponding to the Sylhet division event of "
    "that monsoon."
)

st.subheader("Interpretation")
st.markdown(
    "Flood-only extent is reported in km² and as a fraction of district area. "
    "Validated against the 2024 Sylhet event: the dashboard reports "
    "1,301.5 km² flood-only (37.4 % of Sylhet district), which falls within "
    "the published reporting range (60–80 % of Sylhet division submerged at "
    "peak; Sylhet district itself at 30–40 % across the median of the flood "
    "window). A dry-season control test for the same district produces "
    "27.9 km² (0.8 % of district), confirming a 47× contrast between flood "
    "and baseline conditions."
)

st.subheader("Limitations")
st.markdown(
    "- The −16 dB threshold is a population-level value and can produce false "
    "positives over tarmac, recently transplanted rice paddies, and other "
    "smooth or wet surfaces.\n"
    "- Median compositing across the flood window understates true peak "
    "inundation; the dashboard reports a median, not a peak.\n"
    "- The JRC permanent-water threshold (50 % occurrence) is conservative. "
    "Pixels that are water for less than half the year are not classified as "
    "permanent and may contribute to the flood-only count during normal "
    "seasonal expansion of the haor wetlands."
)

st.markdown("**Methodological note on projection handling.**")
st.markdown(
    "Sentinel-1 has 10 m UTM as its native projection; JRC GSW has 30 m "
    "EPSG:4326. Earth Engine operations that mix these two trigger internal "
    "resampling that produces fractional values at binary-region boundaries. "
    "Algebraic operations such as `.Not()` followed by multiplication, or "
    "`.subtract()` between binary images, propagate these fractional values "
    "incorrectly through area summation, producing flood extents that "
    "under-count the true value by approximately 75 %. This module avoids "
    "the artifact by using `updateMask(permanent_water.eq(0))` for the "
    "boolean exclusion. Diagnosing this required parallel evaluation of four "
    "algebraically equivalent formulations; only `updateMask` and `where` "
    "produced correct results."
)

st.divider()

st.header("4. Coastal Salinity (Bouaziz SI)")

st.warning(
    "This indicator is a visible-band brightness proxy, not a calibrated "
    "soil-salinity measurement. Read the Limitations subsection before "
    "interpreting the displayed values."
)

st.subheader("Description")
st.markdown(
    "The Bouaziz Salinity Index measures soil and surface brightness in the "
    "visible spectrum. Salt crusts on bare or sparsely vegetated soil brighten "
    "visible-band reflectance, so the index is sensitive to salt accumulation. "
    "It is also sensitive to other drivers of visible brightness, which is the "
    "source of its principal limitation."
)

st.subheader("Formula")
st.latex(r"\mathrm{SI} = \sqrt{B_{2} \times B_{4}}")
st.markdown(
    "where $B_{2}$ is Sentinel-2 Blue (492 nm) and $B_{4}$ is Sentinel-2 Red "
    "(665 nm), both in surface reflectance units. The dashboard reports two "
    "values per district per year: the dry-season mean (1 March – 31 May) and "
    "the monsoon-season mean (1 July – 30 September)."
)

st.subheader("Data Sources")
st.markdown(
    "- `COPERNICUS/S2_SR_HARMONIZED`, `CLOUDY_PIXEL_PERCENTAGE < 60`, QA60 "
    "cloud and cirrus mask.\n"
    "- Two seasonal composites per year, reduction at 100 m scale.\n"
    "- Restricted to 19 coastal districts of Bangladesh defined by the "
    "standard government coastal-zone designation."
)

st.subheader("Interpretation")
st.markdown(
    "The salt-crust hypothesis predicts dry-season SI to exceed monsoon-season "
    "SI in saline coastal soils, because dry conditions expose salt crusts "
    "that brighten visible bands while monsoon conditions dilute and mask "
    "them. The dashboard exposes the seasonal pair so users can read the "
    "contrast directly. The contrast is the intended signal, but it is not a "
    "clean salinity signal. See Limitations."
)

st.subheader("Limitations")
st.markdown(
    "This is the most epistemically fragile indicator in the dashboard. It is "
    "not calibrated against ground-truth soil electrical conductivity "
    "measurements."
)
st.markdown(
    "The seasonal contrast is influenced by multiple drivers, only one of "
    "which is salinity:"
)
st.markdown(
    "- **Rice phenology.** Boro rice harvest in late dry season (April–May) "
    "leaves bare bright fields. Aman rice during the monsoon produces dense "
    "green canopy that darkens visible bands. Both shifts independently push "
    "dry SI up and monsoon SI down.\n"
    "- **Aquaculture.** Shrimp ponds in southwestern coastal districts cover "
    "large fractions of district area year-round. Their water surfaces darken "
    "visible bands. The seasonal management cycle of these ponds (filling, "
    "draining, harvest) further influences seasonal SI.\n"
    "- **Cloud-mask survivor bias.** The < 60 % cloud filter retains a "
    "substantially smaller scene count during the monsoon than during the dry "
    "season. Monsoon scenes that pass the filter are atmospherically atypical "
    "days, often with elevated aerosol loading, which can artificially "
    "brighten visible bands."
)

st.markdown("**Empirical observation supporting the caveat.**")
st.markdown(
    "As of the 2024 calendar year, the dashboard reports for Khulna (a "
    "heavily aquaculture-dominated southwestern coastal district): dry-season "
    "SI ≈ 0.084, monsoon-season SI ≈ 0.104 — inverted relative to the "
    "salt-crust hypothesis. For Cox's Bazar (a southeastern coastal district "
    "with conventional Aman-dominant agriculture): dry-season SI ≈ 0.113, "
    "monsoon-season SI ≈ 0.097 — consistent with the hypothesis. Both "
    "directions are explainable by local geography. Neither should be read "
    "as evidence that one district is more saline than the other."
)

st.markdown("**Relationship to Sarkar et al. 2023.**")
st.markdown(
    "The project specification originally cited Sarkar et al. (2023, "
    "*Scientific Reports* 13:17056) as the salinity methodology source. That "
    "paper uses Landsat 8 OLI imagery (not Sentinel-2), 13 spectral indices "
    "as features, and three machine-learning models (Random Forest, "
    "Bagging+RF, Artificial Neural Network) trained on 241 ground-truth "
    "electrical conductivity samples from a single upazila in Satkhira "
    "District. Their best model achieves AUC 0.921 and produces a 5-class "
    "soil salinity zone map. We did not replicate Sarkar's pipeline; we have "
    "neither ground-truth samples nor a pre-trained network. We adopted the "
    "Bouaziz Salinity Index from the broader remote-sensing literature "
    "(Bouaziz et al. 2011) as a defensible proxy that uses bands distinct "
    "from NDVI and NDMI and that has a transparent published formula. The ML "
    "approach in Sarkar et al. is a stronger methodology than ours; "
    "reproducing it would require ground-truth EC data we do not have access "
    "to."
)

st.divider()

st.header("Cross-Cutting Notes")

st.markdown(
    "- All Sentinel-2-based indicators (NDVI, NDMI, salinity) are subject to "
    "cloud-cover gaps during the monsoon. Sentinel-1 SAR (used for flood) is "
    "the only sensor in this dashboard that is unaffected by cloud cover.\n"
    "- Earth Engine operations on images with different native projections "
    "require careful method selection, as documented in the Flood section. "
    "The pattern is general: use `updateMask` or `where` for boolean "
    "operations between differently-projected images; avoid `.Not()` chained "
    "with multiplication and `.subtract()` between binary images.\n"
    "- The dashboard runs on the Earth Engine Community Tier (free for "
    "non-commercial use). Aggressive caching of district-level results "
    "minimizes repeat compute; cold-cache district selections take 20–30 "
    "seconds, warm cache returns instantly."
)

st.divider()

st.header("References")

st.markdown(
    "- Sarkar, S. K., et al. (2023). Coupling of machine learning and remote "
    "sensing for soil salinity mapping in coastal area of Bangladesh. "
    "*Scientific Reports*, 13, 17056. "
    "https://doi.org/10.1038/s41598-023-44132-4\n"
    "- Bouaziz, M., Matschullat, J., & Gloaguen, R. (2011). Improved remote "
    "sensing detection of soil salinity from a semi-arid climate in Northeast "
    "Brazil. *Comptes Rendus Geoscience*, 343(11–12), 795–803.\n"
    "- Pekel, J.-F., Cottam, A., Gorelick, N., & Belward, A. S. (2016). "
    "High-resolution mapping of global surface water and its long-term "
    "changes. *Nature*, 540, 418–422. (Source for JRC Global Surface Water "
    "dataset.)\n"
    "- Thomas et al. (2019). *Remote Sensing*, 11, 1581. Cited in project "
    "documentation as the source for the Bangladesh-validated −16 dB SAR "
    "water threshold; full author list and title not recorded in the project "
    "specification.\n"
    "- Sentinel-1 GRD (`COPERNICUS/S1_GRD`) — European Space Agency, "
    "distributed via Google Earth Engine.\n"
    "- Sentinel-2 Surface Reflectance Harmonized "
    "(`COPERNICUS/S2_SR_HARMONIZED`) — European Space Agency, distributed "
    "via Google Earth Engine.\n"
    "- FAO/GAUL/2015 administrative boundaries, level 2 — Food and "
    "Agriculture Organization of the United Nations."
)
