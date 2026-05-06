"""Bilingual string lookup with optional Streamlit awareness."""
from __future__ import annotations

import json
import sys
from pathlib import Path

AVAILABLE_LANGUAGES: list[tuple[str, str]] = [
    ("en", "English"),
    ("bn", "বাংলা"),
]

_DEFAULT_LANGUAGE = "en"
_STRINGS_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "strings.json"
)
_STRINGS_CACHE: dict | None = None


def load_strings() -> dict:
    global _STRINGS_CACHE
    if _STRINGS_CACHE is None:
        with _STRINGS_PATH.open(encoding="utf-8") as f:
            _STRINGS_CACHE = json.load(f)
    return _STRINGS_CACHE


def _active_language() -> str:
    if "streamlit" not in sys.modules:
        return _DEFAULT_LANGUAGE
    try:
        import streamlit as st

        return st.session_state.get("language", _DEFAULT_LANGUAGE)
    except Exception:
        return _DEFAULT_LANGUAGE


def t(key: str) -> str:
    strings = load_strings()
    entry = strings.get(key)
    if entry is None:
        return key
    locale = _active_language()
    value = entry.get(locale)
    if value:
        return value
    fallback = entry.get(_DEFAULT_LANGUAGE)
    if fallback:
        return fallback
    return key


def language_selector_sidebar() -> None:
    import streamlit as st

    codes = [code for code, _ in AVAILABLE_LANGUAGES]
    labels = {code: name for code, name in AVAILABLE_LANGUAGES}
    st.sidebar.radio(
        "Language / ভাষা",
        codes,
        format_func=lambda code: labels[code],
        key="language",
    )
