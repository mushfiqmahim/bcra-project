"""Smoke test for atlas.i18n (no Earth Engine, Streamlit not required)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from atlas.i18n import load_strings, t


def main() -> None:
    strings = load_strings()
    assert isinstance(strings, dict) and strings, (
        "strings.json should parse to a non-empty dict"
    )
    print(f"load_strings: OK ({len(strings)} keys)")

    for key, entry in strings.items():
        assert isinstance(entry, dict), (
            f"{key}: value must be a dict, got {type(entry).__name__}"
        )
        assert "en" in entry, f"{key}: missing 'en' key"
        assert "bn" in entry, f"{key}: missing 'bn' key"
    print("structural integrity: OK (every entry has 'en' and 'bn' keys)")

    for key, entry in strings.items():
        en = entry["en"]
        assert isinstance(en, str) and en, (
            f"{key}: 'en' must be a non-empty string, got {en!r}"
        )
    print("English values: OK (every 'en' is a non-empty string)")

    for key, entry in strings.items():
        bn = entry["bn"]
        assert bn is None or (isinstance(bn, str) and bn), (
            f"{key}: 'bn' must be null or a non-empty string, got {bn!r}"
        )
    print("Bangla values: OK (every 'bn' is null or non-empty)")

    title = t("app.title")
    assert isinstance(title, str) and title, (
        f"t('app.title') should return non-empty string, got {title!r}"
    )
    print(f"t('app.title') -> {title!r}: OK")

    fallback = t("nonexistent.key.xyz")
    assert fallback == "nonexistent.key.xyz", (
        f"missing-key lookup should return the key itself, got {fallback!r}"
    )
    print("t('nonexistent.key.xyz') -> returns the key: OK")

    print(f"\nSummary: {len(strings)} keys in strings.json; all assertions pass.")


if __name__ == "__main__":
    main()
