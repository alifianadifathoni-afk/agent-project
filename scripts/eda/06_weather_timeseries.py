"""Weather time series analysis.

Computes monthly and seasonal aggregations, year-over-year comparisons,
and cumulative weather metrics.

Usage:
    python scripts/eda/06_weather_timeseries.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import load_weather, export_json, export_csv

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


def compute_monthly_aggregates(weather_df: pd.DataFrame) -> pd.DataFrame:
    """Compute monthly temperature and precipitation averages."""
    df = weather_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%b")

    monthly = (
        df.groupby(["field_id", "year", "month", "month_name"])
        .agg(
            {
                "T2M": "mean",
                "T2M_MAX": "mean",
                "T2M_MIN": "mean",
                "PRECTOTCORR": "sum",
                "ALLSKY_SFC_SW_DWN": "sum",
                "RH2M": "mean",
            }
        )
        .reset_index()
    )

    monthly.columns = [
        "field_id",
        "year",
        "month",
        "month_name",
        "temp_mean",
        "temp_max",
        "temp_min",
        "precip_total",
        "solar_total",
        "humidity_mean",
    ]

    return monthly


def compute_seasonal_summary(weather_df: pd.DataFrame) -> pd.DataFrame:
    """Compute growing season (May-Sep) vs dormant season summary."""
    df = weather_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    df["season"] = df["month"].apply(lambda x: "growing" if x in [5, 6, 7, 8, 9] else "dormant")

    seasonal = (
        df.groupby(["field_id", "year", "season"])
        .agg(
            {
                "T2M": "mean",
                "T2M_MAX": "mean",
                "T2M_MIN": "mean",
                "PRECTOTCORR": "sum",
                "ALLSKY_SFC_SW_DWN": "sum",
            }
        )
        .reset_index()
    )

    seasonal.columns = [
        "field_id",
        "year",
        "season",
        "temp_mean",
        "temp_max",
        "temp_min",
        "precip_total",
        "solar_total",
    ]

    return seasonal


def compute_yearly_comparison(weather_df: pd.DataFrame) -> pd.DataFrame:
    """Compare weather metrics across years."""
    df = weather_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year

    yearly = (
        df.groupby(["field_id", "year"])
        .agg(
            {
                "T2M": "mean",
                "T2M_MAX": "mean",
                "T2M_MIN": "mean",
                "PRECTOTCORR": "sum",
                "ALLSKY_SFC_SW_DWN": "sum",
                "RH2M": "mean",
            }
        )
        .reset_index()
    )

    yearly.columns = [
        "field_id",
        "year",
        "temp_annual_mean",
        "temp_annual_max",
        "temp_annual_min",
        "precip_annual_total",
        "solar_annual_total",
        "humidity_annual_mean",
    ]

    return yearly


def compute_cumulative_gdd(weather_df: pd.DataFrame, base_temp: float = 10.0) -> pd.DataFrame:
    """Compute cumulative Growing Degree Days."""
    df = weather_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year

    df["gdd"] = ((df["T2M_MIN"] + df["T2M_MAX"]) / 2 - base_temp).clip(lower=0)
    df["gdd_cumulative"] = df.groupby(["field_id", "year"])["gdd"].cumsum()

    gdd_by_year = (
        df.groupby(["field_id", "year"]).agg({"gdd": "sum", "gdd_cumulative": "max"}).reset_index()
    )

    gdd_by_year.columns = ["field_id", "year", "total_gdd", "max_gdd_cumulative"]

    return gdd_by_year


def create_monthly_plot(monthly_df: pd.DataFrame, output_dir: str) -> None:
    """Create monthly temperature trend plot."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    avg_monthly = monthly_df.groupby(["month", "month_name"])["temp_mean"].mean().reset_index()
    avg_monthly = avg_monthly.sort_values("month")

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.bar(avg_monthly["month_name"], avg_monthly["temp_mean"], color="steelblue", alpha=0.7)
    ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Month")
    ax.set_ylabel("Average Temperature (°C)")
    ax.set_title("Monthly Average Temperature (2022-2024)", fontsize=14, fontweight="bold")

    plt.tight_layout()
    plt.savefig(f"{output_dir}/monthly_temperature_trend.png", dpi=300, bbox_inches="tight")
    plt.close()

    print(f"  Saved: monthly_temperature_trend.png")


def create_yearly_comparison_plot(yearly_df: pd.DataFrame, output_dir: str) -> None:
    """Create yearly precipitation comparison."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    yearly_totals = yearly_df.groupby("year")["precip_annual_total"].mean()

    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(
        yearly_totals.index.astype(str),
        yearly_totals.values,
        color=["#3498db", "#2ecc71", "#e74c3c"],
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("Average Annual Precipitation (mm)")
    ax.set_title("Year-over-Year Precipitation Comparison", fontsize=14, fontweight="bold")

    for bar, val in zip(bars, yearly_totals.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 20,
            f"{val:.0f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    plt.tight_layout()
    plt.savefig(f"{output_dir}/yearly_precipitation_comparison.png", dpi=300, bbox_inches="tight")
    plt.close()

    print(f"  Saved: yearly_precipitation_comparison.png")


def run_time_series_analysis(
    weather_path: str = "output/weather_50_fields_2022_2024.csv",
    output_dir: str = "output/eda/weather",
) -> dict:
    """Run full weather time series analysis."""
    print("Loading weather data...")
    df = load_weather(weather_path)
    print(f"  Loaded {len(df)} daily records")

    print("\n[1/5] Computing monthly aggregates...")
    monthly = compute_monthly_aggregates(df)
    monthly_path = f"{output_dir}/monthly_temperature.csv"
    Path(monthly_path).parent.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(monthly_path, index=False)
    print(f"  Saved: monthly_temperature.csv ({len(monthly)} records)")

    print("\n[2/5] Computing seasonal summaries...")
    seasonal = compute_seasonal_summary(df)
    seasonal_path = f"{output_dir}/seasonal_summary.csv"
    seasonal.to_csv(seasonal_path, index=False)
    print(f"  Saved: seasonal_summary.csv ({len(seasonal)} records)")

    print("\n[3/5] Computing yearly comparisons...")
    yearly = compute_yearly_comparison(df)
    yearly_path = f"{output_dir}/yearly_comparison.csv"
    yearly.to_csv(yearly_path, index=False)
    print(f"  Saved: yearly_comparison.csv ({len(yearly)} records)")

    print("\n[4/5] Computing cumulative GDD...")
    gdd = compute_cumulative_gdd(df)
    gdd_path = f"{output_dir}/gdd_by_year.csv"
    gdd.to_csv(gdd_path, index=False)
    print(f"  Saved: gdd_by_year.csv ({len(gdd)} records)")

    print("\n[5/5] Creating visualizations...")
    create_monthly_plot(monthly, output_dir)
    create_yearly_comparison_plot(yearly, output_dir)

    summary = {
        "n_fields": df["field_id"].nunique(),
        "n_years": df["date"].dt.year.nunique(),
        "date_range": f"{df['date'].min()} to {df['date'].max()}",
        "avg_annual_temp": round(yearly["temp_annual_mean"].mean(), 1),
        "avg_annual_precip": round(yearly["precip_annual_total"].mean(), 0),
        "avg_gdd": round(gdd["total_gdd"].mean(), 0),
    }

    export_json(summary, f"{output_dir}/summary.json")
    print(f"  Saved: summary.json")

    return summary


def main():
    """Run weather time series analysis."""
    print("=" * 60)
    print("Weather Time Series Analysis")
    print("=" * 60)

    summary = run_time_series_analysis()

    print("\n" + "=" * 60)
    print("Time Series Analysis Complete")
    print("=" * 60)
    print(f"\nFields analyzed: {summary['n_fields']}")
    print(f"Years: {summary['n_years']}")
    print(f"Date range: {summary['date_range']}")
    print(f"Average annual temperature: {summary['avg_annual_temp']}°C")
    print(f"Average annual precipitation: {summary['avg_annual_precip']}mm")
    print(f"Average GDD: {summary['avg_gdd']}")


if __name__ == "__main__":
    main()
