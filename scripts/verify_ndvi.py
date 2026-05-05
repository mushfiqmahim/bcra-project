"""Smoke test for atlas.ndvi.ndvi_timeseries."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from atlas.ee_client import init_ee
from atlas.ndvi import ndvi_timeseries


def main() -> None:
    init_ee()

    for district in ("Rangpur", "Khulna"):
        df = ndvi_timeseries(district, months=12)
        print(f"\n{district}:")
        print(df)
        non_null = int(df["ndvi"].notna().sum())
        assert non_null >= 9, (
            f"{district}: only {non_null}/12 months non-null (need >= 9)"
        )
        print(f"{district}: {non_null}/12 non-null months OK")


if __name__ == "__main__":
    main()
