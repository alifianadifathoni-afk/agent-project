#!/usr/bin/env python3
"""Download USDA NASS Crop Sequence Boundaries for Michigan fields."""

import os
os.environ["AWS_NO_SIGN_REQUEST"] = "YES"

import geopandas as gpd
import pandas as pd

CSB_S3_PATH = "s3://usda-nass-csb/csb_parquet/"

MICHIGAN_BBOX = {
    "min_lat": 41.5,
    "max_lat": 44.5,
    "min_lon": -87.5,
    "max_lon": -82.0,
}


def download_fields(count: int = 50, crops: list[str] = None, output_path: str = None):
    """Download field boundaries from USDA NASS Crop Sequence Boundaries.
    
    Parameters:
        count: Number of fields to download
        crops: List of crops to filter (corn, soybeans, wheat, cotton)
        output_path: Path to save GeoJSON
        
    Returns:
        GeoDataFrame with field boundaries
    """
    print(f"Loading USDA NASS Crop Sequence Boundaries from S3...")
    
    try:
        gdf = gpd.read_file(CSB_S3_PATH)
        print(f"Loaded {len(gdf)} total fields")
    except Exception as e:
        print(f"S3 access failed: {e}")
        print("Trying alternative approach...")
        return None
    
    print(f"Columns: {gdf.columns.tolist()}")
    print(f"CRS: {gdf.crs}")
    
    # Get centroids for filtering
    gdf["centroid"] = gdf.geometry.centroid
    gdf["lat"] = gdf.centroid.y
    gdf["lon"] = gdf.centroid.x
    
    # Filter to Michigan bounding box
    michigan = gdf[
        (gdf["lat"] >= MICHIGAN_BBOX["min_lat"]) &
        (gdf["lat"] <= MICHIGAN_BBOX["max_lat"]) &
        (gdf["lon"] >= MICHIGAN_BBOX["min_lon"]) &
        (gdf["lon"] <= MICHIGAN_BBOX["max_lon"])
    ].copy()
    print(f"Fields in Michigan bbox: {len(michigan)}")
    
    if len(michigan) == 0:
        print("No fields found in Michigan bounding box")
        return None
    
    # Filter by crop if specified
    if crops and len(crops) > 0:
        # Check what crop columns exist
        crop_cols = [c for c in michigan.columns if 'crop' in c.lower()]
        print(f"Crop columns: {crop_cols}")
        
        # Try common crop column names
        crop_col = None
        for col in ['crop_name', 'crop', 'primary_crop', 'crop_2023']:
            if col in michigan.columns:
                crop_col = col
                break
        
        if crop_col:
            crops_lower = [c.lower() for c in crops]
            michigan = michigan[michigan[crop_col].str.lower().isin(crops_lower)].copy()
            print(f"Fields after crop filter: {len(michigan)}")
    
    # Take requested count
    result = michigan.head(count).copy()
    
    # Clean up temporary columns
    if "centroid" in result.columns:
        result = result.drop(columns=["centroid"])
    
    print(f"Selected {len(result)} fields")
    
    # Save if output path specified
    if output_path:
        result.to_file(output_path, driver="GeoJSON")
        print(f"Saved to {output_path}")
    
    return result


if __name__ == "__main__":
    import sys
    
    fields = download_fields(
        count=50,
        crops=["corn", "soybeans", "wheat"],
        output_path="data/michigan_fields_raw.geojson"
    )
    
    if fields is not None:
        print(f"\nField summary:")
        print(f"Total fields: {len(fields)}")
        print(f"Columns: {fields.columns.tolist()[:10]}...")
