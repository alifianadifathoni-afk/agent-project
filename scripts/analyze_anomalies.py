"""Analyze anomalies in 2024 weather data vs historical averages.

Creates:
- data/michigan_weather_anomaly.png
- Console output of detected anomalies

Run:
    python scripts/analyze_anomalies.py
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

DATA_DIR = Path("data")
HISTORICAL_CSV = DATA_DIR / "michigan_weather_historical.csv"
CURRENT_CSV = DATA_DIR / "michigan_weather_2024.csv"
OUTPUT_PNG = DATA_DIR / "michigan_weather_anomaly.png"


def load_data():
    """Load current and historical weather data."""
    historical = pd.read_csv(HISTORICAL_CSV, parse_dates=["date"])
    current = pd.read_csv(CURRENT_CSV, parse_dates=["date"])
    return historical, current


def calculate_monthly_averages(historical: pd.DataFrame) -> pd.DataFrame:
    """Calculate monthly historical averages (2019-2023)."""
    historical = historical.copy()
    historical["month"] = historical["date"].dt.month
    historical["year"] = historical["date"].dt.year

    # Filter to growing season (May-Sep)
    growing_season_months = [5, 6, 7, 8, 9]
    hs_data = historical[historical["month"].isin(growing_season_months)]

    # Monthly averages by field
    monthly_avg = (
        hs_data.groupby(["field_id", "month"])
        .agg(
            {
                "T2M": "mean",
                "T2M_MAX": "mean",
                "T2M_MIN": "mean",
                "PRECTOTCORR": "mean",
            }
        )
        .reset_index()
    )

    return monthly_avg


def calculate_current_monthly(current: pd.DataFrame) -> pd.DataFrame:
    """Calculate monthly totals for 2024."""
    current = current.copy()
    current["month"] = current["date"].dt.month

    monthly = (
        current.groupby(["field_id", "month"])
        .agg(
            {
                "T2M": "mean",
                "T2M_MAX": "mean",
                "T2M_MIN": "mean",
                "PRECTOTCORR": "sum",  # Total precipitation
            }
        )
        .reset_index()
    )

    return monthly


def detect_anomalies(current: pd.DataFrame, historical_avg: pd.DataFrame) -> dict:
    """Detect weather anomalies."""
    anomalies = {
        "late_frost": [],
        "heat_stress": [],
        "dry_spell": [],
        "rainfall_deficit": [],
    }

    current = current.copy()
    current["month"] = current["date"].dt.month

    for field_id in current["field_id"].unique():
        field_data = current[current["field_id"] == field_id].sort_values("date")

        # 1. Late frost detection (T2M_MIN < 0°C after May 15)
        spring = field_data[
            (field_data["date"] >= "2024-05-15") & (field_data["date"] <= "2024-06-15")
        ]
        frost_days = spring[spring["T2M_MIN"] < 0]
        if len(frost_days) > 0:
            anomalies["late_frost"].append(
                {
                    "field": field_id,
                    "dates": frost_days["date"].dt.strftime("%Y-%m-%d").tolist(),
                    "min_temps": frost_days["T2M_MIN"].tolist(),
                }
            )

        # 2. Heat stress (T2M_MAX > 32°C for 5+ consecutive days)
        high_temp = field_data[field_data["T2M_MAX"] > 32].sort_values("date")
        if len(high_temp) >= 5:
            anomalies["heat_stress"].append(
                {"field": field_id, "count": len(high_temp), "max_temp": high_temp["T2M_MAX"].max()}
            )

        # 3. Dry spell detection (10+ consecutive days with < 1mm rain)
        dry_days = field_data[field_data["PRECTOTCORR"] < 1].sort_values("date")
        if len(dry_days) >= 10:
            # Find longest consecutive streak
            dry_dates = dry_days["date"]
            consecutive = []
            current_streak = [dry_dates.iloc[0]]

            for i in range(1, len(dry_dates)):
                if (dry_dates.iloc[i] - dry_dates.iloc[i - 1]).days == 1:
                    current_streak.append(dry_dates.iloc[i])
                else:
                    if len(current_streak) >= 10:
                        consecutive.append(current_streak.copy())
                    current_streak = [dry_dates.iloc[i]]

            if len(current_streak) >= 10:
                consecutive.append(current_streak)

            if consecutive:
                longest = max(consecutive, key=len)
                anomalies["dry_spell"].append(
                    {
                        "field": field_id,
                        "start": min(longest).strftime("%Y-%m-%d"),
                        "end": max(longest).strftime("%Y-%m-%d"),
                        "days": len(longest),
                    }
                )

        # 4. Rainfall deficit (monthly 2024 < 80% of historical)
        current_monthly = (
            current[current["field_id"] == field_id].groupby("month")["PRECTOTCORR"].sum()
        )
        hist_monthly = historical_avg[historical_avg["field_id"] == field_id].set_index("month")[
            "PRECTOTCORR"
        ]

        for month in current_monthly.index:
            hist_val = hist_monthly.get(month, 0)
            curr_val = current_monthly.get(month, 0)
            if hist_val > 0 and curr_val < 0.8 * hist_val:
                deficit_pct = ((hist_val - curr_val) / hist_val) * 100
                anomalies["rainfall_deficit"].append(
                    {
                        "field": field_id,
                        "month": month,
                        "2024": round(curr_val, 1),
                        "historical": round(hist_val, 1),
                        "deficit_pct": round(deficit_pct, 1),
                    }
                )

    return anomalies


def create_anomaly_visualization(
    current: pd.DataFrame, historical_avg: pd.DataFrame, anomalies: dict, output_path: Path
):
    """Create anomaly visualization - bar chart of monthly precipitation."""

    # Aggregate across all fields
    current_monthly = current.copy()
    current_monthly["month"] = current_monthly["date"].dt.month
    current_agg = current_monthly.groupby("month")["PRECTOTCORR"].sum().reset_index()
    current_agg["type"] = "2024"

    hist_agg = historical_avg.groupby("month")["PRECTOTCORR"].mean().reset_index()
    hist_agg["PRECTOTCORR"] = hist_agg["PRECTOTCORR"] * 3  # Scale for 3 fields
    hist_agg["type"] = "Historical (5-yr avg)"

    months = [5, 6, 7, 8, 9]
    month_labels = ["May", "Jun", "Jul", "Aug", "Sep"]

    fig, ax = plt.subplots(figsize=(12, 7))

    x = range(len(months))
    width = 0.35

    # Historical bars
    hist_vals = [
        hist_agg[hist_agg["month"] == m]["PRECTOTCORR"].values[0]
        if m in hist_agg["month"].values
        else 0
        for m in months
    ]
    current_vals = [
        current_agg[current_agg["month"] == m]["PRECTOTCORR"].values[0]
        if m in current_agg["month"].values
        else 0
        for m in months
    ]

    bars1 = ax.bar(
        [i - width / 2 for i in x],
        hist_vals,
        width,
        label="Historical (2019-2023)",
        color="#4a90d9",
        alpha=0.7,
    )
    bars2 = ax.bar(
        [i + width / 2 for i in x], current_vals, width, label="2024", color="#e74c3c", alpha=0.7
    )

    # Add deficit percentage labels
    for i, m in enumerate(months):
        h_val = hist_vals[i]
        c_val = current_vals[i]
        if h_val > 0:
            deficit = ((h_val - c_val) / h_val) * 100
            if deficit > 0:
                ax.annotate(
                    f"-{deficit:.0f}%",
                    xy=(i + width / 2, c_val),
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    color="#c0392b",
                    fontweight="bold",
                )

    # Highlight drought conditions with asterisks for significant deficits
    for i, m in enumerate(months):
        h_val = hist_vals[i]
        c_val = current_vals[i]
        if h_val > 0 and c_val < 0.8 * h_val:
            ax.annotate("⚠️", xy=(i, max(h_val, c_val) + 15), ha="center", fontsize=14)

    ax.set_ylabel("Total Precipitation (mm)", fontsize=12)
    ax.set_xlabel("Month", fontsize=12)
    ax.set_title(
        "2024 Growing Season Precipitation vs 5-Year Historical Average\nMichigan Corn Fields",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(month_labels)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    ax.set_ylim(0, max(hist_vals + current_vals) * 1.2)

    # Add anomaly text box
    anomaly_text = []
    if anomalies["rainfall_deficit"]:
        anomaly_text.append("Rainfall Deficits Detected:")
        for d in anomalies["rainfall_deficit"]:
            month_name = month_labels[d["month"] - 5] if d["month"] >= 5 else str(d["month"])
            anomaly_text.append(
                f"  • {d['field']} - {month_name}: {d['deficit_pct']}% below normal"
            )

    if anomalies["dry_spell"]:
        anomaly_text.append("\nProlonged Dry Spells:")
        for d in anomalies["dry_spell"]:
            anomaly_text.append(f"  • {d['field']}: {d['days']} days ({d['start']} to {d['end']})")

    if anomalies["heat_stress"]:
        anomaly_text.append("\nHeat Stress Events:")
        for h in anomalies["heat_stress"]:
            anomaly_text.append(
                f"  • {h['field']}: {h['count']} days >32°C (max {h['max_temp']:.1f}°C)"
            )

    if anomaly_text:
        textstr = "\n".join(anomaly_text)
        props = dict(boxstyle="round", facecolor="#ffeaa7", alpha=0.8)
        ax.text(
            0.02,
            0.98,
            textstr,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment="top",
            bbox=props,
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved visualization to: {output_path}")
    plt.close()


def main():
    print("Loading data...")
    historical, current = load_data()

    print("Calculating monthly historical averages...")
    monthly_avg = calculate_monthly_averages(historical)

    print("Detecting anomalies...")
    anomalies = detect_anomalies(current, monthly_avg)

    print("\n=== ANOMALY DETECTION RESULTS ===")

    if anomalies["rainfall_deficit"]:
        print("\n📉 RAINFALL DEFICITS:")
        for d in anomalies["rainfall_deficit"]:
            month_name = ["", "", "", "", "May", "Jun", "Jul", "Aug", "Sep"][d["month"]]
            print(
                f"  {d['field']} - {month_name}: {d['2024']}mm vs {d['historical']}mm historical ({d['deficit_pct']}% deficit)"
            )

    if anomalies["dry_spell"]:
        print("\n🌵 PROLONGED DRY SPELLS:")
        for d in anomalies["dry_spell"]:
            print(f"  {d['field']}: {d['days']} days ({d['start']} to {d['end']})")

    if anomalies["heat_stress"]:
        print("\n🔥 HEAT STRESS:")
        for h in anomalies["heat_stress"]:
            print(f"  {h['field']}: {h['count']} days above 32°C (max: {h['max_temp']:.1f}°C)")

    if anomalies["late_frost"]:
        print("\�❄️ LATE FROST:")
        for f in anomalies["late_frost"]:
            print(f"  {f['field']}: {len(f['dates'])} frost days in late spring")

    if not any(anomalies.values()):
        print("No significant anomalies detected.")

    print("\nCreating visualization...")
    create_anomaly_visualization(current, monthly_avg, anomalies, OUTPUT_PNG)
    print("Done!")


if __name__ == "__main__":
    main()
