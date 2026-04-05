"""Download Michigan field boundaries for weather analysis.

Creates:
- data/michigan_fields.geojson

Run:
    python scripts/download_michigan_fields.py
"""

import os
from pathlib import Path

try:
    import geopandas as gpd
    import numpy as np
    from shapely.geometry import Polygon
except ImportError:
    print("Installing dependencies...")
    import subprocess

    subprocess.run(["pip", "install", "geopandas", "shapely", "matplotlib"], check=True)
    import geopandas as gpd
    import numpy as np
    from shapely.geometry import Polygon

# Output directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Michigan Lower Peninsula approximate bounds
MICHIGAN_BOUNDS = {
    "lat_min": 41.7,
    "lat_max": 45.7,
    "lon_min": -90.5,
    "lon_max": -82.0,
}


def download_michigan_fields(count: int = 3, output_path: str = "data/michigan_fields.geojson"):
    """Download synthetic Michigan corn field boundaries.

    Args:
        count: Number of fields to generate
        output_path: Path to save GeoJSON
    """
    np.random.seed(42)

    data = {
        "field_id": [],
        "region": [],
        "crop_name": [],
        "area_acres": [],
        "state": [],
        "county": [],
        "geometry": [],
    }

    counties = ["Isabella", "Midland", "Gratiot", "Clinton", "Shiawassee", "Saginaw", "Tuscola"]

    for i in range(count):
        # Generate random field within Michigan bounds
        center_lat = np.random.uniform(MICHIGAN_BOUNDS["lat_min"], MICHIGAN_BOUNDS["lat_max"])
        center_lon = np.random.uniform(MICHIGAN_BOUNDS["lon_min"], MICHIGAN_BOUNDS["lon_max"])

        # Field size ~5-15 acres
        size_deg = np.random.uniform(0.003, 0.006)

        coords = [
            (center_lon - size_deg, center_lat - size_deg),
            (center_lon + size_deg, center_lat - size_deg),
            (center_lon + size_deg, center_lat + size_deg),
            (center_lon - size_deg, center_lat + size_deg),
            (center_lon - size_deg, center_lat - size_deg),
        ]

        polygon = Polygon(coords)
        # Convert deg² to acres (approximate)
        area_acres = polygon.area * 24710538

        field_id = f"MI26{(i + 1):05d}"

        data["field_id"].append(field_id)
        data["region"].append("michigan")
        data["crop_name"].append("corn")
        data["area_acres"].append(round(area_acres, 2))
        data["state"].append("MI")
        data["county"].append(np.random.choice(counties))
        data["geometry"].append(polygon)

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")

    # Save to file
    gdf.to_file(output_path, driver="GeoJSON")
    print(f"Downloaded {len(gdf)} Michigan corn fields")
    print(f"Saved to: {output_path}")
    print(f"\nField summary:")
    for _, row in gdf.iterrows():
        print(f"  {row['field_id']}: {row['area_acres']:.1f} acres in {row['county']} County")

    return gdf


if __name__ == "__main__":
    fields = download_michigan_fields(count=3)
