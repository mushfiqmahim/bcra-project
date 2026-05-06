"""BCRA methodology page: formulas, data sources, interpretation, limitations."""
import streamlit as st

from atlas.i18n import language_selector_sidebar, t

st.set_page_config(page_title="BCRA — Methodology", layout="wide")

language_selector_sidebar()

st.title(t("methodology.title"))

st.markdown(t("methodology.overview.paragraph_1"))
st.markdown(t("methodology.overview.paragraph_2"))

st.divider()

st.header(t("methodology.ndvi.heading"))

st.subheader(t("methodology.subheader.description"))
st.markdown(t("methodology.ndvi.description"))

st.subheader(t("methodology.subheader.formula"))
st.latex(r"\mathrm{NDVI} = \frac{B_{8} - B_{4}}{B_{8} + B_{4}}")
st.markdown(t("methodology.ndvi.formula_caption"))

st.subheader(t("methodology.subheader.data_sources"))
st.markdown(
    "\n".join(
        [
            f"- {t('methodology.ndvi.data_sources.bullet_1')}",
            f"- {t('methodology.ndvi.data_sources.bullet_2')}",
            f"- {t('methodology.ndvi.data_sources.bullet_3')}",
        ]
    )
)

st.subheader(t("methodology.subheader.interpretation"))
st.markdown(t("methodology.ndvi.interpretation"))

st.subheader(t("methodology.subheader.limitations"))
st.markdown(
    "\n".join(
        [
            f"- {t('methodology.ndvi.limitations.bullet_1')}",
            f"- {t('methodology.ndvi.limitations.bullet_2')}",
            f"- {t('methodology.ndvi.limitations.bullet_3')}",
            f"- {t('methodology.ndvi.limitations.bullet_4')}",
        ]
    )
)

st.divider()

st.header(t("methodology.ndmi.heading"))

st.subheader(t("methodology.subheader.description"))
st.markdown(t("methodology.ndmi.description"))

st.subheader(t("methodology.subheader.formula"))
st.latex(r"\mathrm{NDMI} = \frac{B_{8} - B_{11}}{B_{8} + B_{11}}")
st.markdown(t("methodology.ndmi.formula_caption"))

st.subheader(t("methodology.subheader.data_sources"))
st.markdown(f"- {t('methodology.ndmi.data_sources.bullet_1')}")

st.subheader(t("methodology.subheader.interpretation"))
st.markdown(t("methodology.ndmi.interpretation"))

st.subheader(t("methodology.subheader.limitations"))
st.markdown(
    "\n".join(
        [
            f"- {t('methodology.ndmi.limitations.bullet_1')}",
            f"- {t('methodology.ndmi.limitations.bullet_2')}",
            f"- {t('methodology.ndmi.limitations.bullet_3')}",
            f"- {t('methodology.ndmi.limitations.bullet_4')}",
        ]
    )
)

st.divider()

st.header(t("methodology.flood.heading"))

st.subheader(t("methodology.subheader.description"))
st.markdown(t("methodology.flood.description"))

st.subheader(t("methodology.flood.method.heading"))
st.markdown(
    f"{t('methodology.flood.method.intro')}\n\n"
    f"1. {t('methodology.flood.method.step_1')}\n"
    f"2. {t('methodology.flood.method.step_2')}\n"
    f"3. {t('methodology.flood.method.step_3')}\n"
    f"4. {t('methodology.flood.method.step_4')}\n"
    f"5. {t('methodology.flood.method.step_5')}"
)

st.subheader(t("methodology.subheader.data_sources"))
st.markdown(
    "\n".join(
        [
            f"- {t('methodology.flood.data_sources.bullet_1')}",
            f"- {t('methodology.flood.data_sources.bullet_2')}",
            f"- {t('methodology.flood.data_sources.bullet_3')}",
            f"- {t('methodology.flood.data_sources.bullet_4')}",
        ]
    )
)

st.subheader(t("methodology.subheader.interpretation"))
st.markdown(t("methodology.flood.interpretation"))

st.subheader(t("methodology.subheader.limitations"))
st.markdown(
    "\n".join(
        [
            f"- {t('methodology.flood.limitations.bullet_1')}",
            f"- {t('methodology.flood.limitations.bullet_2')}",
            f"- {t('methodology.flood.limitations.bullet_3')}",
        ]
    )
)

st.markdown(t("methodology.flood.projection_note.heading"))
st.markdown(t("methodology.flood.projection_note.body"))

st.divider()

st.header(t("methodology.salinity.heading"))

st.warning(t("methodology.salinity.warning"))

st.subheader(t("methodology.subheader.description"))
st.markdown(t("methodology.salinity.description"))

st.subheader(t("methodology.subheader.formula"))
st.latex(r"\mathrm{SI} = \sqrt{B_{2} \times B_{4}}")
st.markdown(t("methodology.salinity.formula_caption"))

st.subheader(t("methodology.subheader.data_sources"))
st.markdown(
    "\n".join(
        [
            f"- {t('methodology.salinity.data_sources.bullet_1')}",
            f"- {t('methodology.salinity.data_sources.bullet_2')}",
            f"- {t('methodology.salinity.data_sources.bullet_3')}",
        ]
    )
)

st.subheader(t("methodology.subheader.interpretation"))
st.markdown(t("methodology.salinity.interpretation"))

st.subheader(t("methodology.subheader.limitations"))
st.markdown(t("methodology.salinity.limitations.intro_1"))
st.markdown(t("methodology.salinity.limitations.intro_2"))
st.markdown(
    "\n".join(
        [
            f"- {t('methodology.salinity.limitations.bullet_1')}",
            f"- {t('methodology.salinity.limitations.bullet_2')}",
            f"- {t('methodology.salinity.limitations.bullet_3')}",
        ]
    )
)

st.markdown(t("methodology.salinity.empirical.heading"))
st.markdown(t("methodology.salinity.empirical.body"))

st.markdown(t("methodology.salinity.sarkar.heading"))
st.markdown(t("methodology.salinity.sarkar.body"))

st.divider()

st.header(t("methodology.cross_cutting.heading"))

st.markdown(
    "\n".join(
        [
            f"- {t('methodology.cross_cutting.bullet_1')}",
            f"- {t('methodology.cross_cutting.bullet_2')}",
            f"- {t('methodology.cross_cutting.bullet_3')}",
        ]
    )
)

st.divider()

st.header(t("methodology.references.heading"))

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
