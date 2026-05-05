"""Earth Engine initialization for local dev and Streamlit Cloud."""
from __future__ import annotations

import json

import ee

_DEFAULT_PROJECT = "earth-engine-project-495404"


def init_ee() -> None:
    """Initialize Earth Engine.

    Uses a service account when running on Streamlit Cloud (credentials in
    st.secrets["gcp_service_account"]), otherwise falls back to the local
    user OAuth flow established by `earthengine authenticate`.
    """
    creds_dict = _read_service_account()
    if creds_dict is not None:
        credentials = ee.ServiceAccountCredentials(
            email=creds_dict["client_email"],
            key_data=json.dumps(creds_dict),
        )
        ee.Initialize(credentials=credentials, project=_DEFAULT_PROJECT)
    else:
        ee.Initialize(project=_DEFAULT_PROJECT)


def _read_service_account() -> dict | None:
    try:
        import streamlit as st
    except ImportError:
        return None
    try:
        if "gcp_service_account" not in st.secrets:
            return None
        return dict(st.secrets["gcp_service_account"])
    except Exception:
        return None


def test_connection():
    return ee.Number(10).add(5).getInfo()
