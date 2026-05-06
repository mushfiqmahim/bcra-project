"""Shared UI chrome (sidebar layout and page footer) for the BCRA app."""
from __future__ import annotations

from atlas.i18n import language_selector_sidebar, t

GITHUB_URL = "https://github.com/mushfiqmahim/bcra-project"


def sidebar_chrome() -> None:
    import streamlit as st

    st.sidebar.divider()
    st.sidebar.markdown(f"**{t('app.title')}**")
    st.sidebar.caption(t("sidebar.project_tagline"))
    st.sidebar.divider()
    language_selector_sidebar()
    st.sidebar.divider()
    st.sidebar.caption(
        f"[{t('common.github_link_text')}]({GITHUB_URL})"
    )


def app_footer() -> None:
    import streamlit as st

    st.divider()
    st.caption(
        f"{t('app.title')} · "
        f"[{t('common.github_link_text')}]({GITHUB_URL}) · "
        f"[{t('footer.methodology_link_text')}](/methodology)"
    )
