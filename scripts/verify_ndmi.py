"""Smoke test for atlas.moisture.ndmi_timeseries."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from atlas.ee_client import init_ee
from atlas.moisture import ndmi_timeseries


def main() -> None:
    init_ee()

    end_date = pd.Timestamp.today().normalize().strftime("%Y-%m-%d")

    for district in ("Rangpur", "Khulna"):
        df = ndmi_timeseries(district, 12, end_date)
        print(f"\n{district}:")
        print(df)
        non_null = int(df["ndmi"].notna().sum())
        assert non_null >= 9, (
            f"{district}: only {non_null}/12 months non-null (need >= 9)"
        )
        values = df["ndmi"].dropna()
        assert values.between(-0.5, 0.7).all(), (
            f"{district}: NDMI values out of [-0.5, 0.7] sanity range: "
            f"{values.tolist()}"
        )
        print(
            f"{district}: {non_null}/12 non-null months OK; "
            f"all values within [-0.5, 0.7]"
        )


if __name__ == "__main__":
    main()
