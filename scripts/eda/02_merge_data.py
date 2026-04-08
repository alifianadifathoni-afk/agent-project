"""Merge all agricultural data layers into a single dashboard-ready dataset.

This script joins:
- Field boundaries
- Soil data (dominant soil per field)
- Weather data (seasonal aggregates)
- CDL crop type (2024)
- NDVI data

Usage:
    python scripts/eda/02_merge_data.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    load_fields,
    load_soil,
    load_weather,
    load_cdl,
    load_ndvi,
    get_dominant_soil,
    aggregate_weather,
    export_csv,
)

import pandas as pd


def merge_all_data(
    fields_path: str = "output/fields_50_cornbelt.geojson",
    soil_path: str = "output/soil_data_50_fields.csv",
    weather_path: str = "output/weather_50_fields_2022_2024.csv",
    cdl_path: str = "output/cdl_50_fields.csv",
    ndvi_path: str = "output/ndvi_50_fields.csv",
    output_path: str = "output/eda/merged_eda_data.csv",
) -> pd.DataFrame:
    """Merge all data layers into a single DataFrame."""
    print("Loading data layers...")

    fields_gdf = load_fields(fields_path)
    fields_df = fields_gdf.drop(columns=["geometry"])
    print(f"  Fields: {len(fields_df)} records")

    soil_df = load_soil(soil_path)
    dominant_soil = get_dominant_soil(soil_df)
    soil_cols = [
        "field_id",
        "muname",
        "drainagecl",
        "om_r",
        "ph1to1h2o_r",
        "awc_r",
        "claytotal_r",
        "sandtotal_r",
        "silttotal_r",
        "dbthirdbar_r",
        "cec7_r",
    ]
    soil_agg = dominant_soil[soil_cols].copy()
    print(f"  Soil: {len(soil_agg)} records (dominant)")

    weather_df = load_weather(weather_path)
    weather_agg = aggregate_weather(weather_df)
    print(f"  Weather: {len(weather_agg)} records (seasonal aggregate)")

    cdl_df = load_cdl(cdl_path)
    cdl_2024 = cdl_df[cdl_df["year"] == 2024][
        ["field_id", "crop_code", "crop_name", "dominant_pct"]
    ].copy()
    cdl_2024 = cdl_2024.rename(columns={"crop_name": "cdl_crop_2024"})
    print(f"  CDL: {len(cdl_2024)} records (2024)")

    ndvi_df = load_ndvi(ndvi_path)
    ndvi_cols = ["field_id", "ndvi_peak", "ndvi_mean", "ndvi_std"]
    ndvi_agg = ndvi_df[ndvi_cols].copy()
    print(f"  NDVI: {len(ndvi_agg)} records")

    print("\nMerging data...")
    merged = fields_df.merge(soil_agg, on="field_id", how="left")
    merged = merged.merge(weather_agg, on="field_id", how="left")
    merged = merged.merge(cdl_2024, on="field_id", how="left")
    merged = merged.merge(ndvi_agg, on="field_id", how="left")

    merged = merged.rename(
        columns={
            "crop_name": "assigned_crop",
            "muname": "soil_type",
            "om_r": "soil_om_pct",
            "ph1to1h2o_r": "soil_ph",
            "drainagecl": "soil_drainage",
            "claytotal_r": "soil_clay_pct",
            "sandtotal_r": "soil_sand_pct",
            "silttotal_r": "soil_silt_pct",
            "awc_r": "soil_awc",
            "dbthirdbar_r": "soil_bulk_density",
            "cec7_r": "soil_cec",
        }
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    export_csv(merged, output_path)

    print(f"\n✓ Merged data saved to: {output_path}")
    print(f"  Total records: {len(merged)}")
    print(f"  Total columns: {len(merged.columns)}")
    print(f"\nColumns: {merged.columns.tolist()}")

    return merged


def main():
    """Run data merge."""
    print("=" * 60)
    print("EDA Data Merge Pipeline")
    print("=" * 60)

    merged = merge_all_data()

    print("\n" + "=" * 60)
    print("Merge complete!")
    print("=" * 60)

    print("\nData summary:")
    print(f"  Fields by crop: {merged.groupby('assigned_crop').size().to_dict()}")
    print(f"  Fields by state: {merged.groupby('state').size().to_dict()}")
    print(f"  Soil types: {merged['soil_type'].nunique()}")
    print(f"  Soil drainage: {merged['soil_drainage'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
