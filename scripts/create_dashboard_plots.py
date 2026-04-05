"""Create weather dashboard plots for row crops.

Creates:
- output/dashboard_assets/weather_trends.png

Features:
1. Cumulative precipitation - 2024 vs 5-year historical
2. Cumulative GDD - 2024 vs 5-year historical with crop stage markers

Run:
    python scripts/create_dashboard_plots.py
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches

DATA_DIR = Path("data")
HISTORICAL_CSV = DATA_DIR / "michigan_weather_historical.csv"
CURRENT_CSV = DATA_DIR / "michigan_weather_2024.csv"
OUTPUT_DIR = Path("output/dashboard_assets")
OUTPUT_PNG = OUTPUT_DIR / "weather_trends.png"

# Field colors
FIELD_COLORS = {
    "MI2600001": "#1f77b4",  # Blue
    "MI2600002": "#2ca02c",  # Green
    "MI2600003": "#d62728",  # Red
}

# Corn GDD thresholds (base 10°C, cap 30°C)
CORN_STAGES = {
    "Emergence": 150,
    "6-Leaf": 475,
    "12-Leaf": 870,
    "Tasseling": 1150,
    "Silking": 1400,
    "Dent": 1875,
    "Maturity": 2500,
}


def calculate_gdd(
    df: pd.DataFrame, base_temp: float = 10.0, cap_temp: float = 30.0
) -> pd.DataFrame:
    """Calculate daily GDD and add as column."""
    df = df.copy()
    t_avg = ((df["T2M_MAX"] + df["T2M_MIN"]) / 2).clip(upper=cap_temp)
    df["GDD"] = (t_avg - base_temp).clip(lower=0)
    return df


def calculate_cumulative(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate cumulative GDD and precipitation per field."""
    df = df.copy()
    df["GDD_cumulative"] = df.groupby("field_id")["GDD"].cumsum()
    df["PRECTOTCORR_cumulative"] = df.groupby("field_id")["PRECTOTCORR"].cumsum()
    return df


def load_and_prepare_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and prepare current and historical data."""
    historical = pd.read_csv(HISTORICAL_CSV, parse_dates=["date"])
    current = pd.read_csv(CURRENT_CSV, parse_dates=["date"])

    # Calculate GDD
    historical = calculate_gdd(historical)
    current = calculate_gdd(current)

    # Cumulative metrics
    historical = calculate_cumulative(historical)
    current = calculate_cumulative(current)

    return historical, current


def calculate_historical_averages(historical: pd.DataFrame) -> pd.DataFrame:
    """Calculate historical cumulative averages by day of year."""
    historical = historical.copy()
    historical["day_of_year"] = historical["date"].dt.dayofyear

    # Get 2024 day range (May 1 = 121 to Sep 30 = 274)
    day_range = range(121, 275)

    # Aggregate across fields and calculate mean by day_of_year
    agg = (
        historical.groupby(["field_id", "day_of_year"])
        .agg(
            {
                "GDD_cumulative": "mean",
                "PRECTOTCORR_cumulative": "mean",
            }
        )
        .reset_index()
    )

    # Average across fields
    daily_avg = (
        agg.groupby("day_of_year")
        .agg(
            {
                "GDD_cumulative": "mean",
                "PRECTOTCORR_cumulative": "mean",
            }
        )
        .reset_index()
    )

    # Convert day_of_year back to date for 2024
    daily_avg["date"] = pd.to_datetime("2024-01-01") + pd.to_timedelta(
        daily_avg["day_of_year"] - 1, unit="D"
    )
    daily_avg = daily_avg[(daily_avg["date"] >= "2024-05-01") & (daily_avg["date"] <= "2024-09-30")]

    return daily_avg


def create_dashboard_plot(current: pd.DataFrame, historical_avg: pd.DataFrame, output_path: Path):
    """Create combined dashboard visualization."""

    fig, axes = plt.subplots(2, 1, figsize=(14, 12))

    fields = current["field_id"].unique()

    # === PANEL 1: Cumulative Precipitation ===
    ax1 = axes[0]

    # Plot historical average
    ax1.plot(
        historical_avg["date"],
        historical_avg["PRECTOTCORR_cumulative"],
        linewidth=2.5,
        linestyle="--",
        color="#888888",
        label="Historical avg (5-yr)",
    )

    # Plot each field
    for field_id in fields:
        field_data = current[current["field_id"] == field_id].sort_values("date")
        color = FIELD_COLORS.get(field_id, "#888888")

        ax1.plot(
            field_data["date"],
            field_data["PRECTOTCORR_cumulative"],
            linewidth=2,
            color=color,
            label=field_id,
        )

    ax1.set_ylabel("Cumulative Precipitation (mm)", fontsize=12)
    ax1.set_title(
        "Cumulative Precipitation - 2024 Growing Season vs Historical Average",
        fontsize=14,
        fontweight="bold",
    )
    ax1.legend(loc="upper left", fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)

    # Add final values annotation
    for field_id in fields:
        field_data = current[current["field_id"] == field_id].sort_values("date")
        final_val = field_data["PRECTOTCORR_cumulative"].iloc[-1]
        color = FIELD_COLORS.get(field_id, "#888888")
        ax1.annotate(
            f"{final_val:.0f}mm",
            xy=(field_data["date"].iloc[-1], final_val),
            xytext=(5, 0),
            textcoords="offset points",
            fontsize=9,
            color=color,
            fontweight="bold",
        )

    # === PANEL 2: Cumulative GDD ===
    ax2 = axes[1]

    # Plot historical average
    ax2.plot(
        historical_avg["date"],
        historical_avg["GDD_cumulative"],
        linewidth=2.5,
        linestyle="--",
        color="#888888",
        label="Historical avg (5-yr)",
    )

    # Plot each field
    for field_id in fields:
        field_data = current[current["field_id"] == field_id].sort_values("date")
        color = FIELD_COLORS.get(field_id, "#888888")

        ax2.plot(
            field_data["date"],
            field_data["GDD_cumulative"],
            linewidth=2,
            color=color,
            label=field_id,
        )

    ax2.set_ylabel("Cumulative GDD (base 10°C)", fontsize=12)
    ax2.set_xlabel("Date", fontsize=12)
    ax2.set_title(
        "Cumulative Growing Degree Days - Corn Development Tracking", fontsize=14, fontweight="bold"
    )
    ax2.legend(loc="upper left", fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(bottom=0)

    # Add corn growth stage markers
    stage_colors = ["#27ae60", "#f39c12", "#e74c3c", "#8e44ad"]
    stage_names = ["Emergence", "Tasseling", "Silking", "Maturity"]
    stage_values = [150, 1150, 1400, 2500]

    for gdd_val, stage_name, color in zip(stage_values, stage_names, stage_colors):
        ax2.axhline(y=gdd_val, color=color, linestyle=":", alpha=0.5)

        # Find approximate date when GDD threshold is reached (use average)
        dates_at_stage = []
        for field_id in fields:
            field_data = current[current["field_id"] == field_id].sort_values("date")
            hit = field_data[field_data["GDD_cumulative"] >= gdd_val]
            if len(hit) > 0:
                dates_at_stage.append(hit["date"].iloc[0])

        if dates_at_stage:
            avg_date = pd.Series(dates_at_stage).mean()
            ax2.scatter(
                [avg_date],
                [gdd_val],
                s=100,
                marker="o",
                color=color,
                zorder=5,
                edgecolors="white",
                linewidth=1.5,
            )
            ax2.annotate(
                stage_name,
                xy=(avg_date, gdd_val),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                fontsize=9,
                color=color,
                fontweight="bold",
            )

    # Format x-axis
    for ax in axes:
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved dashboard to: {output_path}")
    plt.close()


def main():
    print("Loading data...")
    historical, current = load_and_prepare_data()

    print("Calculating historical averages...")
    historical_avg = calculate_historical_averages(historical)

    print("Creating dashboard visualization...")
    create_dashboard_plot(current, historical_avg, OUTPUT_PNG)

    # Print summary stats
    print("\n=== DASHBOARD SUMMARY ===")

    for field_id in current["field_id"].unique():
        field_data = current[current["field_id"] == field_id].sort_values("date")
        final_gdd = field_data["GDD_cumulative"].iloc[-1]
        final_precip = field_data["PRECTOTCORR_cumulative"].iloc[-1]

        print(f"\n{field_id}:")
        print(f"  Final cumulative GDD: {final_gdd:.0f}")
        print(f"  Final cumulative precip: {final_precip:.0f}mm")

    print("\nDone!")


if __name__ == "__main__":
    main()
