#!/usr/bin/env python3
"""Download USDA NASS Crop Sequence Boundaries - Clustered 10 fields from SW Michigan."""

import os

os.environ["AWS_NO_SIGN_REQUEST"] = "YES"

import geopandas as gpd
import numpy as np
from itertools import combinations

CSB_S3_PATH = "s3://usda-nass-csb/csb_parquet/"

# Southwest Michigan bounding box (Branch, St. Joseph, Hillsdale counties area)
# This is about ~15-20 miles across
SW_MICHIGAN_BBOX = {
    "min_lat": 41.70,
    "max_lat": 42.15,
    "min_lon": -85.25,
    "max_lon": -84.50,
}


def download_fields(count: int = 50, crops: list[str] = None, output_path: str = None):
    """Download field boundaries from USDA NASS Crop Sequence Boundaries."""
    print("Loading USDA NASS Crop Sequence Boundaries from S3...")

    try:
        gdf = gpd.read_file(CSB_S3_PATH)
        print(f"Loaded {len(gdf)} total fields")
    except Exception as e:
        print(f"S3 access failed: {e}")
        print("Trying alternative approach...")
        return None

    print(f"CRS: {gdf.crs}")

    # Get centroids for filtering
    gdf["centroid"] = gdf.geometry.centroid
    gdf["lat"] = gdf.centroid.y
    gdf["lon"] = gdf.centroid.x

    # Filter to southwest Michigan bounding box
    sw_michigan = gdf[
        (gdf["lat"] >= SW_MICHIGAN_BBOX["min_lat"])
        & (gdf["lat"] <= SW_MICHIGAN_BBOX["max_lat"])
        & (gdf["lon"] >= SW_MICHIGAN_BBOX["min_lon"])
        & (gdf["lon"] <= SW_MICHIGAN_BBOX["max_lon"])
    ].copy()
    print(f"Fields in SW Michigan bbox: {len(sw_michigan)}")

    if len(sw_michigan) == 0:
        print("No fields found in SW Michigan bounding box")
        return None

    # Filter by crop if specified
    if crops and len(crops) > 0:
        crop_cols = [c for c in sw_michigan.columns if "crop" in c.lower()]
        print(f"Crop columns: {crop_cols}")

        crop_col = None
        for col in ["crop_name", "crop", "primary_crop", "crop_2023"]:
            if col in sw_michigan.columns:
                crop_col = col
                break

        if crop_col:
            crops_lower = [c.lower() for c in crops]
            sw_michigan = sw_michigan[sw_michigan[crop_col].str.lower().isin(crops_lower)].copy()
            print(f"Fields after crop filter: {len(sw_michigan)}")

    # Take requested count
    result = sw_michigan.head(count).copy()

    # Clean up temporary columns
    if "centroid" in result.columns:
        result = result.drop(columns=["centroid"])

    print(f"Selected {len(result)} fields")
    return result


def select_closest_fields(gdf: gpd.GeoDataFrame, n: int = 10) -> gpd.GeoDataFrame:
    """Select n fields that are closest to each other based on centroid distances."""
    if len(gdf) <= n:
        print(f"Only {len(gdf)} fields available, returning all")
        return gdf

    # Calculate centroids
    centroids = gdf.geometry.centroid
    coords = np.array([[c.x, c.y] for c in centroids])

    # Calculate pairwise distances
    n_fields = len(gdf)
    dist_matrix = np.zeros((n_fields, n_fields))
    for i in range(n_fields):
        for j in range(i + 1, n_fields):
            dist = np.sqrt((coords[i][0] - coords[j][0])**2 + (coords[i][1] - coords[j][1])**2)
            dist_matrix[i][j] = dist
            dist_matrix[j][i] = dist

    # Find the n fields with minimum total pairwise distance
    # Try all combinations and find the one with minimum total distance
    print(f"Finding {n} closest fields from {n_fields} candidates...")
    
    best_sum = float('inf')
    best_indices = None
    
    # For large n, use greedy approach instead of exhaustive search
    if n_fields > 15:
        # Start with field closest to center
        center_lat = np.mean(coords[:, 1])
        center_lon = np.mean(coords[:, 0])
        distances_to_center = np.sqrt((coords[:, 0] - center_lon)**2 + (coords[:, 1] - center_lat)**2)
        start_idx = np.argmin(distances_to_center)
        
        selected = [start_idx]
        remaining = list(range(n_fields))
        remaining.remove(start_idx)
        
        for _ in range(n - 1):
            # Find closest to the current selection's centroid
            current_centroid = np.mean([coords[i] for i in selected], axis=0)
            distances = np.array([np.sqrt((coords[i][0] - current_centroid[0])**2 + 
                                          (coords[i][1] - current_centroid[1])**2) 
                                 for i in remaining])
            next_idx = remaining[np.argmin(distances)]
            selected.append(next_idx)
            remaining.remove(next_idx)
        
        best_indices = selected
    else:
        # Exhaustively search all combinations
        from itertools import combinations
        for combo in combinations(range(n_fields), n):
            total_dist = sum(dist_matrix[i][j] for i, j in combinations(combo, 2))
            if total_dist < best_sum:
                best_sum = total_dist
                best_indices = list(combo)
    
    print(f"Selected indices: {best_indices}")
    
    result = gdf.iloc[best_indices].copy()
    result = result.reset_index(drop=True)
    
    # Show the counties
    if 'county' in result.columns:
        print(f"Counties: {result['county'].unique().tolist()}")
    
    return result


def main():
    # Download 30 fields from southwest Michigan
    fields = download_fields(
        count=30,
        crops=["corn", "soybeans"],
        output_path=None
    )

    if fields is None:
        print("Failed to download fields")
        return

    print(f"\nDownloaded {len(fields)} fields from SW Michigan")

    # Select 10 closest fields
    clustered_fields = select_closest_fields(fields, n=10)
    print(f"\nSelected {len(clustered_fields)} clustered fields")

    # Display field info
    print("\nField Summary:")
    print(f"Total fields: {len(clustered_fields)}")
    if 'county' in clustered_fields.columns:
        print(f"Counties: {clustered_fields['county'].unique().tolist()}")
    if 'area_acres' in clustered_fields.columns:
        print(f"Total area: {clustered_fields['area_acres'].sum():.1f} acres")

    # Save to GeoJSON
    output_path = "data/michigan_fields.geojson"
    clustered_fields.to_file(output_path, driver="GeoJSON")
    print(f"\nSaved clustered fields to {output_path}")

    # Also show the coordinates range
    bounds = clustered_fields.total_bounds
    print(f"\nBounding box: {bounds[1]:.4f} to {bounds[3]:.4f} N, {bounds[0]:.4f} to {bounds[2]:.4f} W")
    print(f"Spread: {(bounds[2]-bounds[0])*69:.1f} miles (E-W) x {(bounds[3]-bounds[1])*59:.1f} miles (N-S)")


if __name__ == "__main__":
    main()
