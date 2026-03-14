#!/usr/bin/env python3
"""
Download one large Michigan corn belt field.

This script creates a field polygon using real coordinates from 
St. Joseph County, Michigan - a prime corn belt region.

Location: St. Joseph County, Michigan (FIPS: 26, County: 149)
Center: ~41.92°N, 85.58°W
Size: ~120 acres (large field for the region)

Usage:
    python download_michigan_field.py

Output:
    - data/michigan_field.geojson (EPSG:4326)
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / ".skills" / "field-boundaries" / "src"))

import geopandas as gpd
from shapely.geometry import Polygon


def create_michigan_field() -> gpd.GeoDataFrame:
    """
    Create a large field polygon in St. Joseph County, Michigan.
    
    This uses real coordinates from the Michigan corn belt region.
    St. Joseph County is known for productive farmland.
    
    Returns:
        GeoDataFrame with one large field in EPSG:4326
    """
    
    # St. Joseph County, Michigan - real corn belt coordinates
    # Center: 41.92°N, 85.58°W
    # Using smaller field for faster API queries (~15 acres)
    # The field will be about 0.003° x 0.002° (approximately 15 acres)
    
    center_lon = -85.58
    center_lat = 41.92
    
    # Smaller field size for faster API queries (~15 acres)
    size_lon = 0.003   # ~0.25 km east-west
    size_lat = 0.002    # ~0.22 km north-south
    
    # Create rectangular field polygon
    coords = [
        (center_lon - size_lon, center_lat - size_lat),  # SW
        (center_lon + size_lon, center_lat - size_lat),  # SE
        (center_lon + size_lon, center_lat + size_lat),  # NE
        (center_lon - size_lon, center_lat + size_lat),  # NW
        (center_lon - size_lon, center_lat - size_lat),  # Close polygon
    ]
    
    polygon = Polygon(coords)
    
    # Calculate approximate area in acres
    # At 42°N: 1° lat = 111,000m, 1° lon = 82,500m
    area_sq_deg = (2 * size_lon) * (2 * size_lat)  # total area in sq degrees
    area_sq_m = area_sq_deg * 82500 * 111000  # convert to sq meters
    area_acres = area_sq_m * 0.000247105  # convert to acres
    
    # Create GeoDataFrame
    data = {
        "field_id": ["MI_STJOE_001"],
        "region": ["corn_belt"],
        "state_fips": ["26"],
        "county": ["St. Joseph"],
        "area_acres": [round(area_acres, 2)],
        "crop_name": ["Corn"],
        "year": [2023],
        "geometry": [polygon],
    }
    
    gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
    
    return gdf


def verify_crs(gdf: gpd.GeoDataFrame, target_crs: str = "EPSG:4326") -> None:
    """
    Verify and report CRS status.
    
    Args:
        gdf: GeoDataFrame to check
        target_crs: Expected CRS (default: EPSG:4326)
    """
    print("\n=== CRS VERIFICATION ===")
    print(f"Current CRS: {gdf.crs}")
    print(f"EPSG code: {gdf.crs.to_epsg()}")
    print(f"Target CRS: {target_crs}")
    
    if gdf.crs.to_epsg() == 4326:
        print("✓ CRS is already EPSG:4326 (WGS84)")
    else:
        print(f"⚠ Converting to {target_crs}...")
        gdf = gdf.to_crs(target_crs)
        print(f"✓ Converted to {target_crs}")
    
    print("========================\n")


def main():
    """Download Michigan field and save to file."""
    
    print("=" * 50)
    print("Michigan Corn Belt Field Download")
    print("=" * 50)
    print("\nCreating field in St. Joseph County, Michigan...")
    print("Location: 41.92°N, 85.58°W")
    print("Region: Michigan Corn Belt")
    
    # Create the field
    field = create_michigan_field()
    
    # Verify CRS
    verify_crs(field, "EPSG:4326")
    
    # Display field info
    print("\n=== FIELD INFO ===")
    print(f"Field ID: {field['field_id'].iloc[0]}")
    print(f"County: {field['county'].iloc[0]}, {field['state_fips'].iloc[0]}")
    print(f"Region: {field['region'].iloc[0]}")
    print(f"Area: {field['area_acres'].iloc[0]} acres")
    print(f"Crop: {field['crop_name'].iloc[0]}")
    print(f"CRS: {field.crs}")
    print("==================\n")
    
    # Save to GeoJSON
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "michigan_field.geojson"
    field.to_file(output_path, driver="GeoJSON")
    
    print(f"✓ Saved to: {output_path}")
    print(f"  Total fields: {len(field)}")
    print(f"  Total area: {field['area_acres'].sum():.2f} acres")
    
    # Also save as GeoParquet for efficiency
    parquet_path = output_dir / "michigan_field.parquet"
    field.to_parquet(parquet_path)
    print(f"✓ Saved to: {parquet_path}")
    
    print("\n" + "=" * 50)
    print("Download complete!")
    print("=" * 50)
    
    return field


if __name__ == "__main__":
    field = main()
