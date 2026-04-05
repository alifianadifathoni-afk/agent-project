"""Download SSURGO soil data for Michigan corn fields.

Creates:
- data/michigan_soil.csv

Run:
    python scripts/download_soil_spatial.py
"""

import sys
from pathlib import Path

# Add skill to path
sys.path.insert(0, str(Path(__file__).parent.parent / ".opencode/skills/ssurgo-soil/src"))

import geopandas as gpd
from ssurgo_soil import download_soil, get_dominant_soil


def main():
    DATA_DIR = Path("data")
    OUTPUT_CSV = DATA_DIR / "michigan_soil.csv"

    print("Loading field boundaries...")
    fields = gpd.read_file(DATA_DIR / "michigan_fields.geojson")
    print(f"Loaded {len(fields)} fields")

    print("\nDownloading SSURGO soil data...")
    print("(This queries the NRCS Soil Data Access API)")

    soil = download_soil(
        fields, field_id_column="field_id", max_depth_cm=30, output_path=str(OUTPUT_CSV)
    )

    print(f"\nDownloaded {len(soil)} soil records for {soil['field_id'].nunique()} fields")

    # Get dominant soil per field
    dominant = get_dominant_soil(soil)
    print(f"\nDominant soil per field:")
    print(
        dominant[["field_id", "compname", "om_r", "ph1to1h2o_r", "drainagecl"]].to_string(
            index=False
        )
    )

    # Save dominant soil
    dominant.to_csv(DATA_DIR / "michigan_soil_dominant.csv", index=False)
    print(f"\nSaved dominant soil to: {DATA_DIR / 'michigan_soil_dominant.csv'}")


if __name__ == "__main__":
    main()
