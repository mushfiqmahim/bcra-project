"""Smoke test for atlas.flood.flood_extent."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from atlas.ee_client import init_ee
from atlas.flood import flood_extent


def main() -> None:
    init_ee()

    event = flood_extent("Sylhet", "2024-05-25", "2024-06-30")
    print("\nSylhet flood event (2024-05-25 to 2024-06-30):")
    print(f"  flood_only_area_km2:      {event['flood_only_area_km2']:.1f}")
    print(f"  permanent_water_area_km2: {event['permanent_water_area_km2']:.1f}")
    print(f"  flood_total_area_km2:     {event['flood_total_area_km2']:.1f}")
    assert event["flood_only_area_km2"] > 1000, (
        f"Sylhet event: expected flood_only > 1000 km^2, "
        f"got {event['flood_only_area_km2']:.1f}"
    )
    print("Sylhet event flood_only_area_km2 > 1000 OK")

    control = flood_extent("Sylhet", "2024-02-25", "2024-03-31")
    print("\nSylhet dry-season control (2024-02-25 to 2024-03-31):")
    print(f"  flood_only_area_km2:      {control['flood_only_area_km2']:.1f}")
    assert control["flood_only_area_km2"] < 100, (
        f"Dry-season control: expected flood_only < 100 km^2, "
        f"got {control['flood_only_area_km2']:.1f}"
    )
    print("Dry-season flood_only_area_km2 < 100 OK")


if __name__ == "__main__":
    main()
