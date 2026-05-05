"""Smoke test for atlas.salinity.salinity_seasonal."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from atlas.ee_client import init_ee
from atlas.salinity import (
    COASTAL_DISTRICTS,
    is_coastal_district,
    salinity_seasonal,
)


def _format_si(value: float | None) -> str:
    return f"{value:.4f}" if value is not None else "None"


def main() -> None:
    init_ee()

    assert is_coastal_district("Khulna"), "Khulna should be coastal"
    assert not is_coastal_district("Rangpur"), "Rangpur should not be coastal"
    print("is_coastal_district checks OK")

    try:
        salinity_seasonal("Rangpur", 2024)
    except ValueError as e:
        print(f"Non-coastal ValueError raised correctly: {e}")
    else:
        raise AssertionError("Expected ValueError for non-coastal district")

    expected_keys = {
        "dry_season_si",
        "monsoon_season_si",
        "district_name",
        "year",
    }
    for sample in ("Khulna", "Satkhira"):
        result = salinity_seasonal(sample, 2024)
        print(f"\n{sample} 2024: {result}")
        assert set(result.keys()) == expected_keys, (
            f"unexpected keys for {sample}: {result.keys()}"
        )
        for key in ("dry_season_si", "monsoon_season_si"):
            v = result[key]
            assert v is None or 0 <= v <= 0.3, (
                f"{sample} {key} out of [0, 0.3] sanity range: {v}"
            )

    print("\nIterating over all coastal districts:")
    successes = 0
    failures: list[tuple[str, str]] = []
    for district in COASTAL_DISTRICTS:
        try:
            r = salinity_seasonal(district, 2024)
            print(
                f"  OK: {district}: dry={_format_si(r['dry_season_si'])} "
                f"monsoon={_format_si(r['monsoon_season_si'])}"
            )
            successes += 1
        except Exception as e:
            print(f"  FAIL: {district}: {e}")
            failures.append((district, str(e)))

    print(
        f"\nSummary: {successes}/{len(COASTAL_DISTRICTS)} districts succeeded; "
        f"{len(failures)} failed"
    )
    assert successes >= 17, (
        f"Only {successes}/{len(COASTAL_DISTRICTS)} districts resolved in "
        f"FAO GAUL. Failures: {failures}"
    )


if __name__ == "__main__":
    main()
