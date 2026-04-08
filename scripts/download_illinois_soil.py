"""Download SSURGO soil data for Illinois Corn Belt field.

Creates:
- data/soil_illinois_corn.csv

Usage:
    python scripts/download_illinois_soil.py
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).parent.parent / ".opencode" / "skills" / "ssurgo-soil" / "src")
)

import geopandas as gpd
from ssurgo_soil import classify_drainage, get_soil_at_point

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def main():
    print("Loading field boundary...")
    fields = gpd.read_file(DATA_DIR / "field_illinois_corn.geojson")
    field = fields.iloc[0]
    field_id = field["field_id"]

    centroid = field.geometry.centroid
    lon, lat = centroid.x, centroid.y

    print(f"Querying NRCS Soil Data Access API for {field_id}...")
    print(f"  Location: {lat:.4f}°N, {lon:.4f}°W")

    soil = get_soil_at_point(lon=lon, lat=lat, max_depth_cm=30)
    soil["field_id"] = field_id

    dominant = soil.sort_values(["comppct_r", "hzdept_r"], ascending=[False, True]).iloc[0]

    print("\n=== DOMINANT SOIL ===")
    print(f"  Series: {dominant['compname']}")
    print(f"  Map Unit: {dominant['muname']}")
    print(f"  Composition: {dominant['comppct_r']}%")
    print(f"  Drainage: {dominant['drainagecl']} ({classify_drainage(dominant['drainagecl'])})")

    print(f"\n=== SOIL PROPERTIES (0-{dominant['hzdepb_r']}cm) ===")
    print(f"  Organic Matter: {dominant['om_r']}%")
    print(f"  pH: {dominant['ph1to1h2o_r']}")
    print(f"  Clay: {dominant['claytotal_r']}%")
    print(f"  Sand: {dominant['sandtotal_r']}%")
    print(f"  Silt: {dominant['silttotal_r']}%")
    print(f"  Bulk Density: {dominant['dbthirdbar_r']} g/cm³")
    print(f"  CEC: {dominant['cec7_r']} meq/100g")
    print(f"  AWC: {dominant['awc_r']} in/in")

    soil.to_csv(DATA_DIR / "soil_illinois_corn.csv", index=False)
    print(f"\nSaved: {DATA_DIR / 'soil_illinois_corn.csv'}")


if __name__ == "__main__":
    main()
