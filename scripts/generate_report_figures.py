#!/usr/bin/env python3
"""Generate visualization figures for Michigan agricultural analysis report.

This script creates all matplotlib/seaborn figures:
- Weather trends (temperature, precipitation, GDD)
- Soil property distributions and correlations
- CDL crop rotation heatmaps
- Interactive maps
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

plt.style.use("seaborn-v0_8-whitegrid")
sns.set_palette("husl")


def plot_weather_annual_trends(weather_df: pd.DataFrame, output_dir: str):
    """Create annual weather trend plots.

    Parameters:
        weather_df: Processed weather DataFrame
        output_dir: Output directory for figures
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    weather_df["year"] = weather_df["DATE"].dt.year
    yearly = weather_df.groupby("year").agg(
        {"T2M": "mean", "T2M_MAX": "mean", "T2M_MIN": "mean", "PRECTOTCORR": "sum"}
    )

    axes[0, 0].plot(yearly.index, yearly["T2M"], "o-", linewidth=2, markersize=8)
    axes[0, 0].set_xlabel("Year")
    axes[0, 0].set_ylabel("Temperature (°C)")
    axes[0, 0].set_title("Annual Average Temperature")

    axes[0, 1].bar(yearly.index, yearly["PRECTOTCORR"], color="steelblue", alpha=0.7)
    axes[0, 1].set_xlabel("Year")
    axes[0, 1].set_ylabel("Precipitation (mm)")
    axes[0, 1].set_title("Annual Total Precipitation")

    monthly = weather_df.copy()
    monthly["month"] = monthly["DATE"].dt.month
    monthly_avg = monthly.groupby("month")["T2M"].mean()

    axes[1, 0].bar(monthly_avg.index, monthly_avg.values, color="coral", alpha=0.7)
    axes[1, 0].set_xlabel("Month")
    axes[1, 0].set_ylabel("Temperature (°C)")
    axes[1, 0].set_title("Monthly Temperature Pattern")
    axes[1, 0].set_xticks(range(1, 13))

    growing = monthly[monthly["month"].isin([4, 5, 6, 7, 8, 9])]
    non_growing = monthly[~monthly["month"].isin([4, 5, 6, 7, 8, 9])]

    seasons = ["Growing Season\n(Apr-Sep)", "Non-Growing\n(Oct-Mar)"]
    temps = [growing["T2M"].mean(), non_growing["T2M"].mean()]

    axes[1, 1].bar(seasons, temps, color=["forestgreen", "gray"], alpha=0.7)
    axes[1, 1].set_ylabel("Mean Temperature (°C)")
    axes[1, 1].set_title("Growing Season Comparison")

    plt.tight_layout()
    plt.savefig(f"{output_dir}/weather_annual_trends.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_dir}/weather_annual_trends.png")


def plot_weather_timeseries(weather_df: pd.DataFrame, output_dir: str):
    """Create weather time series plot.

    Parameters:
        weather_df: Processed weather DataFrame
        output_dir: Output directory for figures
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    weather_df["rolling_temp"] = weather_df["T2M"].rolling(30, center=True).mean()
    weather_df["rolling_precip"] = weather_df["PRECTOTCORR"].rolling(30, center=True).sum()

    axes[0].plot(weather_df["DATE"], weather_df["T2M"], alpha=0.3, linewidth=0.5)
    axes[0].plot(weather_df["DATE"], weather_df["rolling_temp"], linewidth=2, color="red")
    axes[0].set_ylabel("Temperature (°C)")
    axes[0].set_title("Daily Temperature with 30-day Rolling Average")

    axes[1].bar(weather_df["DATE"], weather_df["PRECTOTCORR"], alpha=0.5, width=1)
    axes[1].plot(weather_df["DATE"], weather_df["rolling_precip"], linewidth=2, color="blue")
    axes[1].set_ylabel("Precipitation (mm)")
    axes[1].set_title("Daily Precipitation with 30-day Rolling Sum")

    plt.tight_layout()
    plt.savefig(f"{output_dir}/weather_timeseries.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_dir}/weather_timeseries.png")


def plot_seasonal_gdd(weather_df: pd.DataFrame, output_dir: str):
    """Create seasonal GDD analysis plot.

    Parameters:
        weather_df: Processed weather DataFrame
        output_dir: Output directory for figures
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    weather_df["year"] = weather_df["DATE"].dt.year
    weather_df["month"] = weather_df["DATE"].dt.month

    monthly_precip = weather_df.groupby("month")["PRECTOTCORR"].sum()
    axes[0, 0].bar(monthly_precip.index, monthly_precip.values, color="steelblue", alpha=0.7)
    axes[0, 0].set_xlabel("Month")
    axes[0, 0].set_ylabel("Total Precipitation (mm)")
    axes[0, 0].set_title("Average Monthly Precipitation")
    axes[0, 0].set_xticks(range(1, 13))

    yearly_gdd = weather_df.groupby("year")["GDD"].sum()
    axes[0, 1].bar(yearly_gdd.index, yearly_gdd.values, color="orange", alpha=0.7)
    axes[0, 1].set_xlabel("Year")
    axes[0, 1].set_ylabel("GDD (degree-days)")
    axes[0, 1].set_title("Growing Degree Days by Year (Base 10°C)")

    growing = weather_df[weather_df["month"].isin([4, 5, 6, 7, 8, 9])]
    growing_precip = growing.groupby("year")["PRECTOTCORR"].sum()
    axes[1, 0].bar(growing_precip.index, growing_precip.values, color="green", alpha=0.7)
    axes[1, 0].set_xlabel("Year")
    axes[1, 0].set_ylabel("Precipitation (mm)")
    axes[1, 0].set_title("Growing Season Precipitation (Apr-Sep)")

    monthly_std = weather_df.groupby("month")["T2M"].std()
    axes[1, 1].bar(monthly_std.index, monthly_std.values, color="purple", alpha=0.5)
    axes[1, 1].set_xlabel("Month")
    axes[1, 1].set_ylabel("Std Dev (°C)")
    axes[1, 1].set_title("Monthly Temperature Variability")
    axes[1, 1].set_xticks(range(1, 13))

    plt.tight_layout()
    plt.savefig(f"{output_dir}/seasonal_gdd_analysis.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_dir}/seasonal_gdd_analysis.png")


def plot_soil_distributions(soil_df: pd.DataFrame, output_dir: str):
    """Create soil property distribution plots.

    Parameters:
        soil_df: Soil DataFrame
        output_dir: Output directory for figures
    """
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    if "ph" in soil_df.columns:
        axes[0, 0].hist(soil_df["ph"], bins=15, color="brown", alpha=0.7, edgecolor="black")
        axes[0, 0].set_xlabel("pH")
        axes[0, 0].set_title("Soil pH Distribution")

    if "om" in soil_df.columns:
        axes[0, 1].hist(soil_df["om"], bins=15, color="darkgreen", alpha=0.7, edgecolor="black")
        axes[0, 1].set_xlabel("Organic Matter (%)")
        axes[0, 1].set_title("Organic Matter Distribution")

    if "clay" in soil_df.columns and "field_id" in soil_df.columns:
        field_clay = soil_df.groupby("field_id")["clay"].mean()
        axes[0, 2].bar(range(len(field_clay)), field_clay.values, color="tan", alpha=0.7)
        axes[0, 2].set_xlabel("Field")
        axes[0, 2].set_ylabel("Clay (%)")
        axes[0, 2].set_title("Clay Content by Field")

    if all(c in soil_df.columns for c in ["sand", "silt", "clay"]):
        avg_texture = [soil_df["sand"].mean(), soil_df["silt"].mean(), soil_df["clay"].mean()]
        axes[1, 0].bar(
            ["Sand", "Silt", "Clay"], avg_texture, color=["yellow", "gray", "brown"], alpha=0.7
        )
        axes[1, 0].set_ylabel("Percentage (%)")
        axes[1, 0].set_title("Average Soil Texture")

    if "drainage_class" in soil_df.columns and "ph" in soil_df.columns:
        drainage_ph = soil_df.groupby("drainage_class")["ph"].mean()
        axes[1, 1].barh(drainage_ph.index, drainage_ph.values, color="blue", alpha=0.5)
        axes[1, 1].set_xlabel("pH")
        axes[1, 1].set_title("pH by Drainage Class")

    if "cec" in soil_df.columns and "clay" in soil_df.columns:
        axes[1, 2].scatter(soil_df["clay"], soil_df["cec"], alpha=0.6, c="green")
        axes[1, 2].set_xlabel("Clay (%)")
        axes[1, 2].set_ylabel("CEC (meq/100g)")
        axes[1, 2].set_title("CEC vs Clay Content")

        z = np.polyfit(soil_df["clay"], soil_df["cec"], 1)
        p = np.poly1d(z)
        axes[1, 2].plot(
            soil_df["clay"].sort_values(),
            p(soil_df["clay"].sort_values()),
            "r--",
            linewidth=2,
            label=f"r={soil_df['clay'].corr(soil_df['cec']):.2f}",
        )
        axes[1, 2].legend()

    plt.tight_layout()
    plt.savefig(f"{output_dir}/soil_distributions.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_dir}/soil_distributions.png")


def plot_soil_correlation(soil_df: pd.DataFrame, output_dir: str):
    """Create soil correlation heatmap.

    Parameters:
        soil_df: Soil DataFrame
        output_dir: Output directory for figures
    """
    props = ["ph", "om", "clay", "sand", "silt", "cec", "awc"]
    available = [c for c in props if c in soil_df.columns]

    if len(available) < 2:
        print("Insufficient data for correlation plot")
        return

    corr = soil_df[available].corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap="RdBu_r", center=0, square=True, fmt=".2f", linewidths=0.5)
    plt.title("Soil Properties Correlation Matrix")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/soil_correlation.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_dir}/soil_correlation.png")


def plot_cdl_analysis(cdl_df: pd.DataFrame, output_dir: str):
    """Create CDL analysis plots.

    Parameters:
        cdl_df: CDL DataFrame
        output_dir: Output directory for figures
    """
    year_cols = [
        c
        for c in cdl_df.columns
        if "cdl_" in c.lower() or (isinstance(c, str) and c.startswith("20") and len(c) == 4)
    ]

    if not year_cols:
        print("No CDL year columns found")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    all_crops = []
    for col in year_cols:
        all_crops.extend(cdl_df[col].tolist())

    crop_counts = pd.Series(all_crops).value_counts().head(10)
    axes[0].barh(range(len(crop_counts)), crop_counts.values, color="green", alpha=0.7)
    axes[0].set_yticks(range(len(crop_counts)))
    axes[0].set_yticklabels([f"Crop {i}" for i in crop_counts.index])
    axes[0].set_xlabel("Count")
    axes[0].set_title("Crop Type Distribution (All Years)")

    if "field_id" in cdl_df.columns:
        fields = cdl_df["field_id"].unique()[:5]
        field_crops = []
        for field in fields:
            crops = cdl_df[cdl_df["field_id"] == field][year_cols].values[0]
            field_crops.append(crops)

        axes[1].imshow(field_crops, aspect="auto", cmap="tab10")
        axes[1].set_xlabel("Year Index")
        axes[1].set_ylabel("Field")
        axes[1].set_title("Crop Distribution by Field")

    plt.tight_layout()
    plt.savefig(f"{output_dir}/cdl_analysis.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_dir}/cdl_analysis.png")


def generate_all_figures(
    weather_csv: str = None,
    soil_csv: str = None,
    cdl_csv: str = None,
    output_dir: str = "docs/project/reports/figures",
):
    """Generate all report figures.

    Parameters:
        weather_csv: Path to weather CSV (optional)
        soil_csv: Path to soil CSV (optional)
        cdl_csv: Path to CDL CSV (optional)
        output_dir: Output directory for figures
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Generating figures in {output_dir}...")

    if weather_csv:
        weather_df = pd.read_csv(weather_csv, parse_dates=["DATE"])

        if "GDD" not in weather_df.columns:
            weather_df["GDD"] = (
                (weather_df["T2M_MAX"].clip(upper=30) + weather_df["T2M_MIN"].clip(lower=10)) / 2
            ) - 10
            weather_df["GDD"] = weather_df["GDD"].clip(lower=0)

        plot_weather_annual_trends(weather_df, output_dir)
        plot_weather_timeseries(weather_df, output_dir)
        plot_seasonal_gdd(weather_df, output_dir)

    if soil_csv:
        soil_df = pd.read_csv(soil_csv)
        plot_soil_distributions(soil_df, output_dir)
        plot_soil_correlation(soil_df, output_dir)

    if cdl_csv:
        cdl_df = pd.read_csv(cdl_csv)
        plot_cdl_analysis(cdl_df, output_dir)

    print("Figure generation complete!")


if __name__ == "__main__":
    import sys

    weather_csv = sys.argv[1] if len(sys.argv) > 1 else None
    soil_csv = sys.argv[2] if len(sys.argv) > 2 else None
    cdl_csv = sys.argv[3] if len(sys.argv) > 3 else None

    generate_all_figures(weather_csv, soil_csv, cdl_csv)
