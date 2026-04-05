"""Generate synthetic NDVI data for Michigan corn fields.

Creates:
- data/michigan_ndvi.tif
- data/michigan_ndvi_stats.csv
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path


def create_simple_ndvi_stats(fields_gdf: gpd.GeoDataFrame, output_csv: Path) -> pd.DataFrame:
    """Create realistic synthetic NDVI values for each field.

    Typical NDVI values for corn:
    - Early season (May): 0.2-0.4
    - Peak season (Jul-Aug): 0.6-0.9
    - Late season (Sep): declining

    This generates July 2024 peak values with realistic variation.
    """

    np.random.seed(42)

    stats = []
    for idx, field in fields_gdf.iterrows():
        field_id = field["field_id"]

        # Base NDVI for healthy corn in July
        base_ndvi = np.random.uniform(0.65, 0.85)

        # Add field-specific variation based on field_id
        if "0001" in field_id:
            # Shiawassee - good conditions
            mean_ndvi = base_ndvi + 0.05
        elif "0002" in field_id:
            # Gratiot - slightly lower (clay soils, more moisture)
            mean_ndvi = base_ndvi
        else:
            # Saginaw - variable
            mean_ndvi = base_ndvi - 0.03

        stats.append(
            {
                "field_id": field_id,
                "mean_ndvi": round(mean_ndvi, 3),
                "min_ndvi": round(mean_ndvi * 0.85, 3),
                "max_ndvi": round(min(0.95, mean_ndvi * 1.1), 3),
                "std_ndvi": round(np.random.uniform(0.05, 0.12), 3),
                "pixel_count": int(field["area_acres"] * 40),  # ~40 pixels per acre at 10m
                "date": "2024-07-15",
                "source": "Sentinel-2 (synthetic)",
            }
        )

    df = pd.DataFrame(stats)
    df.to_csv(output_csv, index=False)
    print(f"Created NDVI statistics: {len(df)} fields")
    print(df.to_string(index=False))

    return df


def main():
    DATA_DIR = Path("data")
    OUTPUT_CSV = DATA_DIR / "michigan_ndvi_stats.csv"

    print("Loading field boundaries...")
    fields = gpd.read_file(DATA_DIR / "michigan_fields.geojson")
    print(f"Loaded {len(fields)} fields")

    print("\nGenerating synthetic NDVI statistics for July 2024...")
    create_simple_ndvi_stats(fields, OUTPUT_CSV)

    print(f"\nSaved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
