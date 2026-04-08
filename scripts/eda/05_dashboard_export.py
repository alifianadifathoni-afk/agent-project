"""Dashboard export - Export data in formats ready for web dashboard.

Exports:
- JSON files for interactive charts
- CSV for data tables
- Summary statistics

Usage:
    python scripts/eda/05_dashboard_export.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import export_json, export_csv, get_column_descriptions
from utils import get_dominant_soil, load_soil, load_weather, load_ndvi, load_cdl

import pandas as pd
import numpy as np
from pathlib import Path


def export_field_summary(df: pd.DataFrame, output_dir: str) -> dict:
    """Export field-level summary for dashboard."""
    summary = []

    for _, row in df.iterrows():
        summary.append(
            {
                "id": row["field_id"],
                "state": row["state"],
                "region": row["region"],
                "crop": row["assigned_crop"],
                "area_acres": row["area_acres"],
                "lat": row["centroid_lat"],
                "lon": row["centroid_lon"],
                "soil": {
                    "type": row.get("soil_type"),
                    "om_pct": row.get("soil_om_pct"),
                    "ph": row.get("soil_ph"),
                    "drainage": row.get("soil_drainage"),
                    "clay_pct": row.get("soil_clay_pct"),
                    "bulk_density": row.get("soil_bulk_density"),
                },
                "weather": {
                    "temp_mean": row.get("gdd_temp_mean"),
                    "precip_total": row.get("gdd_precip_total"),
                    "solar_total": row.get("gdd_solar_total"),
                    "humidity_mean": row.get("gdd_humidity_mean"),
                },
                "ndvi": {
                    "peak": row.get("ndvi_peak"),
                    "mean": row.get("ndvi_mean"),
                    "std": row.get("ndvi_std"),
                },
            }
        )

    export_json(summary, f"{output_dir}/fields.json")
    print(f"  Saved: fields.json ({len(summary)} fields)")

    return {"n_fields": len(summary)}


def export_crop_distribution(df: pd.DataFrame, output_dir: str) -> dict:
    """Export crop distribution data."""
    crop_dist = df["assigned_crop"].value_counts().to_dict()
    state_crop = (
        df.groupby(["state", "assigned_crop"]).size().unstack(fill_value=0).to_dict("index")
    )

    data = {
        "overall": crop_dist,
        "by_state": state_crop,
    }

    export_json(data, f"{output_dir}/crop_distribution.json")
    print(f"  Saved: crop_distribution.json")

    return data


def export_soil_summary(df: pd.DataFrame, output_dir: str) -> dict:
    """Export soil summary statistics."""
    soil_vars = [
        "soil_om_pct",
        "soil_ph",
        "soil_clay_pct",
        "soil_sand_pct",
        "soil_silt_pct",
        "soil_awc",
        "soil_bulk_density",
        "soil_cec",
    ]

    summary = {}
    for var in soil_vars:
        if var in df.columns:
            summary[var] = {
                "mean": round(df[var].mean(), 2),
                "median": round(df[var].median(), 2),
                "std": round(df[var].std(), 2),
                "min": round(df[var].min(), 2),
                "max": round(df[var].max(), 2),
            }

    drainage = df["soil_drainage"].value_counts().to_dict()
    summary["drainage_distribution"] = drainage

    export_json(summary, f"{output_dir}/soil_summary.json")
    print(f"  Saved: soil_summary.json")

    return summary


def export_weather_summary(df: pd.DataFrame, output_dir: str) -> dict:
    """Export weather summary statistics."""
    weather_vars = [
        "gdd_temp_mean",
        "gdd_temp_max",
        "gdd_temp_min",
        "gdd_precip_total",
        "gdd_solar_total",
        "gdd_humidity_mean",
    ]

    summary = {}
    for var in weather_vars:
        if var in df.columns:
            summary[var] = {
                "mean": round(df[var].mean(), 2),
                "median": round(df[var].median(), 2),
                "std": round(df[var].std(), 2),
                "min": round(df[var].min(), 2),
                "max": round(df[var].max(), 2),
            }

    export_json(summary, f"{output_dir}/weather_summary.json")
    print(f"  Saved: weather_summary.json")

    return summary


def export_ndvi_summary(df: pd.DataFrame, output_dir: str) -> dict:
    """Export NDVI summary statistics."""
    ndvi_vars = ["ndvi_peak", "ndvi_mean", "ndvi_std"]

    by_crop = {}
    for crop in df["assigned_crop"].unique():
        crop_df = df[df["assigned_crop"] == crop]
        by_crop[crop] = {
            "mean": round(crop_df["ndvi_mean"].mean(), 3),
            "peak_mean": round(crop_df["ndvi_peak"].mean(), 3),
        }

    overall = {
        var: {
            "mean": round(df[var].mean(), 3),
            "std": round(df[var].std(), 3),
        }
        for var in ndvi_vars
        if var in df.columns
    }

    data = {"overall": overall, "by_crop": by_crop}

    export_json(data, f"{output_dir}/ndvi_summary.json")
    print(f"  Saved: ndvi_summary.json")

    return data


def export_kpis(df: pd.DataFrame, output_dir: str) -> dict:
    """Export KPI data for dashboard cards."""
    kpis = {
        "total_fields": len(df),
        "total_acres": round(df["area_acres"].sum(), 0),
        "avg_field_size": round(df["area_acres"].mean(), 1),
        "n_corn": len(df[df["assigned_crop"] == "corn"]),
        "n_soybeans": len(df[df["assigned_crop"] == "soybeans"]),
        "avg_ndvi_peak": round(df["ndvi_peak"].mean(), 3),
        "avg_soil_om": round(df["soil_om_pct"].mean(), 2),
        "avg_soil_ph": round(df["soil_ph"].mean(), 2),
        "total_precip": round(df["gdd_precip_total"].sum(), 0),
    }

    export_json(kpis, f"{output_dir}/kpis.json")
    print(f"  Saved: kpis.json")

    return kpis


def export_time_series(weather_df: pd.DataFrame, output_dir: str) -> dict:
    """Export time series data for charts."""
    weather_df = weather_df.copy()
    weather_df["date"] = pd.to_datetime(weather_df["date"])
    weather_df["year"] = weather_df["date"].dt.year
    weather_df["month"] = weather_df["date"].dt.month

    monthly = (
        weather_df.groupby(["field_id", "year", "month"])
        .agg(
            {
                "T2M": "mean",
                "PRECTOTCORR": "sum",
            }
        )
        .reset_index()
    )

    monthly_agg = (
        monthly.groupby(["year", "month"])
        .agg(
            {
                "T2M": "mean",
                "PRECTOTCORR": "sum",
            }
        )
        .reset_index()
    )

    monthly_agg["month_name"] = pd.to_datetime(
        monthly_agg["year"].astype(str) + "-" + monthly_agg["month"].astype(str) + "-01"
    ).dt.strftime("%b")

    data = monthly_agg.to_dict("records")
    for d in data:
        d["T2M"] = round(d["T2M"], 1)
        d["PRECTOTCORR"] = round(d["PRECTOTCORR"], 1)

    export_json(data, f"{output_dir}/monthly_weather.json")
    print(f"  Saved: monthly_weather.json")

    return {"n_records": len(data)}


def main():
    """Run dashboard export."""
    print("=" * 60)
    print("Dashboard Export")
    print("=" * 60)

    output_dir = "output/eda/dashboard"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("\nLoading data...")
    df = pd.read_csv("output/eda/merged_eda_data.csv")
    weather_df = pd.read_csv("output/weather_50_fields_2022_2024.csv")

    print("\n[1/7] Exporting field summary...")
    export_field_summary(df, output_dir)

    print("\n[2/7] Exporting crop distribution...")
    export_crop_distribution(df, output_dir)

    print("\n[3/7] Exporting soil summary...")
    export_soil_summary(df, output_dir)

    print("\n[4/7] Exporting weather summary...")
    export_weather_summary(df, output_dir)

    print("\n[5/7] Exporting NDVI summary...")
    export_ndvi_summary(df, output_dir)

    print("\n[6/7] Exporting KPIs...")
    export_kpis(df, output_dir)

    print("\n[7/7] Exporting time series...")
    export_time_series(weather_df, output_dir)

    print("\n" + "=" * 60)
    print("Dashboard Export Complete")
    print("=" * 60)
    print(f"\nOutput directory: {output_dir}")
    print("\nExported files:")
    print("  - fields.json")
    print("  - crop_distribution.json")
    print("  - soil_summary.json")
    print("  - weather_summary.json")
    print("  - ndvi_summary.json")
    print("  - kpis.json")
    print("  - monthly_weather.json")


if __name__ == "__main__":
    main()
