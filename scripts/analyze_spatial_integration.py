"""Merge spatial data: fields + soil + NDVI.

Creates:
- data/michigan_spatial_integration.csv
- data/michigan_spatial_integration.geojson

Run:
    python scripts/analyze_spatial_integration.py
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path


def merge_spatial_data() -> gpd.GeoDataFrame:
    """Merge field boundaries with soil and NDVI data."""

    DATA_DIR = Path("data")

    # Load all data
    print("Loading field boundaries...")
    fields = gpd.read_file(DATA_DIR / "michigan_fields.geojson")
    print(f"  Fields: {len(fields)}")

    print("Loading soil data...")
    soil_all = pd.read_csv(DATA_DIR / "michigan_soil.csv")

    # Get dominant soil (highest comppct_r per field)
    soil = soil_all.sort_values(["field_id", "comppct_r"], ascending=[True, False])
    soil = soil.groupby("field_id").first().reset_index()
    print(f"  Dominant soil: {len(soil)}")

    print("Loading NDVI data...")
    ndvi = pd.read_csv(DATA_DIR / "michigan_ndvi_stats.csv")
    print(f"  NDVI records: {len(ndvi)}")

    # Merge soil into fields
    fields = fields.merge(
        soil[["field_id", "compname", "om_r", "ph1to1h2o_r", "drainagecl", "awc_r", "claytotal_r"]],
        on="field_id",
        how="left",
    )

    # Merge NDVI into fields
    fields = fields.merge(
        ndvi[["field_id", "mean_ndvi", "min_ndvi", "max_ndvi", "std_ndvi", "date"]],
        on="field_id",
        how="left",
    )

    # Rename columns for clarity
    fields = fields.rename(
        columns={
            "compname": "soil_type",
            "om_r": "organic_matter_pct",
            "ph1to1h2o_r": "soil_ph",
            "drainagecl": "drainage_class",
            "awc_r": "water_capacity",
            "claytotal_r": "clay_content_pct",
            "mean_ndvi": "ndvi_mean",
            "min_ndvi": "ndvi_min",
            "max_ndvi": "ndvi_max",
        }
    )

    print(f"\nMerged data: {len(fields)} fields")
    print("\nMerged fields:")
    print(
        fields[
            ["field_id", "county", "soil_type", "organic_matter_pct", "drainage_class", "ndvi_mean"]
        ].to_string(index=False)
    )

    # Save merged data
    output_csv = DATA_DIR / "michigan_spatial_integration.csv"
    fields.drop(columns=["geometry"]).to_csv(output_csv, index=False)
    print(f"\nSaved CSV: {output_csv}")

    # Save GeoJSON for mapping
    output_geojson = DATA_DIR / "michigan_spatial_integration.geojson"
    fields.to_file(output_geojson, driver="GeoJSON")
    print(f"Saved GeoJSON: {output_geojson}")

    return fields


if __name__ == "__main__":
    merge_spatial_data()
