"""Create time series visualization for Michigan weather data.

Creates:
- data/michigan_weather_timeseries.png

Shows:
- Daily temperature (T2M_MAX, T2M_MIN) with 7-day rolling average
- Daily precipitation with 7-day rolling average
- All fields overlaid on one chart

Run:
    python scripts/visualize_michigan_weather.py
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Configuration
DATA_DIR = Path("data")
WEATHER_CSV = DATA_DIR / "michigan_weather_2024.csv"
OUTPUT_PNG = DATA_DIR / "michigan_weather_timeseries.png"

# Field colors
FIELD_COLORS = {
    "MI2600001": "#1f77b4",  # Blue
    "MI2600002": "#2ca02c",  # Green
    "MI2600003": "#d62728",  # Red
}


def load_and_prepare_data(csv_path: Path) -> pd.DataFrame:
    """Load weather data and calculate rolling averages."""
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df = df.sort_values(["field_id", "date"])

    # Calculate 7-day rolling averages per field
    for field_id in df["field_id"].unique():
        mask = df["field_id"] == field_id
        df.loc[mask, "T2M_MAX_7d"] = df.loc[mask, "T2M_MAX"].rolling(7, min_periods=1).mean()
        df.loc[mask, "T2M_MIN_7d"] = df.loc[mask, "T2M_MIN"].rolling(7, min_periods=1).mean()
        df.loc[mask, "PRECTOTCORR_7d"] = (
            df.loc[mask, "PRECTOTCORR"].rolling(7, min_periods=1).mean()
        )

    return df


def create_visualization(df: pd.DataFrame, output_path: Path):
    """Create time series visualization with overlaid fields."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    fields = df["field_id"].unique()

    # === TEMPERATURE PANEL ===
    ax_temp = axes[0]

    for field_id in fields:
        field_data = df[df["field_id"] == field_id]
        color = FIELD_COLORS.get(field_id, "#888888")

        # Daily temperature range (fill)
        ax_temp.fill_between(
            field_data["date"],
            field_data["T2M_MIN"],
            field_data["T2M_MAX"],
            alpha=0.15,
            color=color,
            label=f"{field_id} (daily)",
        )

        # Daily lines (thin)
        ax_temp.plot(
            field_data["date"], field_data["T2M_MAX"], linewidth=0.5, color=color, alpha=0.4
        )
        ax_temp.plot(
            field_data["date"], field_data["T2M_MIN"], linewidth=0.5, color=color, alpha=0.4
        )

        # 7-day rolling average (thicker)
        ax_temp.plot(
            field_data["date"],
            field_data["T2M_MAX_7d"],
            linewidth=2,
            linestyle="--",
            color=color,
            label=f"{field_id} MAX (7d)",
        )
        ax_temp.plot(
            field_data["date"], field_data["T2M_MIN_7d"], linewidth=2, linestyle="--", color=color
        )

    ax_temp.set_ylabel("Temperature (°C)", fontsize=12)
    ax_temp.set_title(
        "Daily Temperature (High/Low) with 7-Day Rolling Average", fontsize=14, fontweight="bold"
    )
    ax_temp.legend(loc="upper right", fontsize=9)
    ax_temp.grid(True, alpha=0.3)
    ax_temp.axhline(10, color="gray", linestyle=":", alpha=0.5, label="Corn base temp (10°C)")
    ax_temp.axhline(30, color="gray", linestyle=":", alpha=0.5)

    # === PRECIPITATION PANEL ===
    ax_precip = axes[1]

    for field_id in fields:
        field_data = df[df["field_id"] == field_id]
        color = FIELD_COLORS.get(field_id, "#888888")

        # Daily precipitation bars
        ax_precip.bar(
            field_data["date"],
            field_data["PRECTOTCORR"],
            width=0.8,
            alpha=0.3,
            color=color,
            label=f"{field_id} (daily)",
        )

        # 7-day rolling average line
        ax_precip.plot(
            field_data["date"],
            field_data["PRECTOTCORR_7d"],
            linewidth=2.5,
            color=color,
            label=f"{field_id} (7d avg)",
        )

    ax_precip.set_ylabel("Precipitation (mm/day)", fontsize=12)
    ax_precip.set_xlabel("Date", fontsize=12)
    ax_precip.set_title(
        "Daily Precipitation with 7-Day Rolling Average", fontsize=14, fontweight="bold"
    )
    ax_precip.legend(loc="upper right", fontsize=9)
    ax_precip.grid(True, alpha=0.3)
    ax_precip.set_ylim(bottom=0)

    # Format x-axis
    for ax in axes:
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved visualization to: {output_path}")
    plt.close()


if __name__ == "__main__":
    print("Loading weather data...")
    df = load_and_prepare_data(WEATHER_CSV)

    print(f"Data loaded: {len(df)} records, {df['field_id'].nunique()} fields")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    print("Creating visualization...")
    create_visualization(df, OUTPUT_PNG)

    print("Done!")
