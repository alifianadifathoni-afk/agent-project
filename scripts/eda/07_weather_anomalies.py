"""Weather anomaly detection.

Detects extreme weather events using Z-score and threshold-based methods.
Flags heat waves, cold snaps, drought conditions, and extreme precipitation.

Usage:
    python scripts/eda/07_weather_anomalies.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from utils import export_json, load_weather

THRESHOLDS = {
    "heat_wave_days": 3,
    "heat_wave_temp": 35.0,
    "cold_snap_days": 3,
    "cold_snap_temp": -10.0,
    "extreme_precip_mm": 50.0,
    "drought_days": 14,
    "drought_precip_mm": 2.0,
    "zscore_threshold": 2.0,
}


def detect_zscore_anomalies(df: pd.DataFrame, z_thresh: float = 2.0) -> pd.DataFrame:
    """Detect anomalies using Z-score method."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    anomalies = []

    for field_id in df["field_id"].unique():
        field_df = df[df["field_id"] == field_id]

        for col in ["T2M", "T2M_MAX", "PRECTOTCORR"]:
            if col not in field_df.columns:
                continue

            values = field_df[col].dropna()
            if len(values) < 10:
                continue

            mean_val = values.mean()
            std_val = values.std()

            if std_val == 0:
                continue

            z_scores = (field_df[col] - mean_val) / std_val

            for idx, row in field_df.iterrows():
                z = z_scores.loc[idx]
                if pd.isna(z):
                    continue

                if abs(z) > z_thresh:
                    anomaly_type = "high" if z > 0 else "low"
                    anomalies.append(
                        {
                            "field_id": field_id,
                            "date": row["date"],
                            "variable": col,
                            "value": row[col],
                            "z_score": round(z, 2),
                            "anomaly_type": f"{col}_{anomaly_type}_zscore",
                            "severity": "extreme" if abs(z) > 3 else "moderate",
                        }
                    )

    return pd.DataFrame(anomalies)


def detect_heat_waves(df: pd.DataFrame, min_days: int = 3, min_temp: float = 35.0) -> pd.DataFrame:
    """Detect heat wave events (consecutive days above threshold)."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    heat_waves = []

    for field_id in df["field_id"].unique():
        field_df = df[df["field_id"] == field_id].sort_values("date")
        field_df["above_threshold"] = field_df["T2M_MAX"] >= min_temp

        field_df["heat_streak"] = (
            field_df["above_threshold"] != field_df["above_threshold"].shift()
        ).cumsum()
        field_df["streak_length"] = field_df.groupby("heat_streak")["above_threshold"].transform(
            lambda x: x.sum() if x.any() else 0
        )

        for streak, group in field_df[field_df["above_threshold"]].groupby("heat_streak"):
            streak_df = group[group["above_threshold"]]
            if len(streak_df) >= min_days:
                heat_waves.append(
                    {
                        "field_id": field_id,
                        "start_date": streak_df["date"].min(),
                        "end_date": streak_df["date"].max(),
                        "duration_days": len(streak_df),
                        "max_temp": streak_df["T2M_MAX"].max(),
                        "avg_temp": streak_df["T2M_MAX"].mean(),
                    }
                )

    return pd.DataFrame(heat_waves)


def detect_cold_snaps(df: pd.DataFrame, min_days: int = 3, max_temp: float = -10.0) -> pd.DataFrame:
    """Detect cold snap events (consecutive days below threshold)."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    cold_snaps = []

    for field_id in df["field_id"].unique():
        field_df = df[df["field_id"] == field_id].sort_values("date")
        field_df["below_threshold"] = field_df["T2M_MIN"] <= max_temp

        field_df["cold_streak"] = (
            field_df["below_threshold"] != field_df["below_threshold"].shift()
        ).cumsum()

        for streak, group in field_df[field_df["below_threshold"]].groupby("cold_streak"):
            if len(group) >= min_days:
                cold_snaps.append(
                    {
                        "field_id": field_id,
                        "start_date": group["date"].min(),
                        "end_date": group["date"].max(),
                        "duration_days": len(group),
                        "min_temp": group["T2M_MIN"].min(),
                        "avg_temp": group["T2M_MIN"].mean(),
                    }
                )

    return pd.DataFrame(cold_snaps)


def detect_extreme_precipitation(df: pd.DataFrame, threshold_mm: float = 50.0) -> pd.DataFrame:
    """Detect extreme precipitation events."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    extreme = df[df["PRECTOTCORR"] >= threshold_mm].copy()

    result = (
        extreme.groupby("field_id")
        .agg({"date": ["min", "max", "count"], "PRECTOTCORR": ["max", "sum", "mean"]})
        .reset_index()
    )

    result.columns = [
        "field_id",
        "first_extreme_date",
        "last_extreme_date",
        "n_events",
        "max_precip",
        "total_precip",
        "avg_precip",
    ]

    return result


def detect_drought_periods(
    df: pd.DataFrame, min_days: int = 14, max_precip_mm: float = 2.0
) -> pd.DataFrame:
    """Detect drought periods (low precipitation)."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    drought_periods = []

    for field_id in df["field_id"].unique():
        field_df = df[df["field_id"] == field_id].sort_values("date")
        field_df["dry"] = field_df["PRECTOTCORR"] < max_precip_mm

        field_df["dry_streak"] = (field_df["dry"] != field_df["dry"].shift()).cumsum()

        for streak, group in field_df[field_df["dry"]].groupby("dry_streak"):
            if len(group) >= min_days:
                drought_periods.append(
                    {
                        "field_id": field_id,
                        "start_date": group["date"].min(),
                        "end_date": group["date"].max(),
                        "duration_days": len(group),
                        "total_precip": group["PRECTOTCORR"].sum(),
                        "avg_daily_precip": group["PRECTOTCORR"].mean(),
                    }
                )

    return pd.DataFrame(drought_periods)


def create_anomaly_summary_plot(anomalies_df: pd.DataFrame, output_path: str) -> None:
    """Create visualization of anomaly counts by type."""
    if anomalies_df.empty:
        print("  No anomalies to plot")
        return

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    counts = anomalies_df.groupby("anomaly_type").size().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    counts.plot(kind="barh", ax=ax, color="coral")

    ax.set_xlabel("Count")
    ax.set_ylabel("Anomaly Type")
    ax.set_title("Weather Anomaly Counts by Type", fontsize=14, fontweight="bold")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"  Saved: {Path(output_path).name}")


def create_extreme_events_plot(
    heat_waves: pd.DataFrame,
    cold_snaps: pd.DataFrame,
    extreme_precip: pd.DataFrame,
    output_dir: str,
) -> None:
    """Create summary plot of extreme events."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    if not heat_waves.empty:
        axes[0].hist(heat_waves["duration_days"], bins=10, color="red", alpha=0.7)
        axes[0].set_xlabel("Duration (days)")
        axes[0].set_ylabel("Count")
        axes[0].set_title("Heat Waves")

    if not cold_snaps.empty:
        axes[1].hist(cold_snaps["duration_days"], bins=10, color="blue", alpha=0.7)
        axes[1].set_xlabel("Duration (days)")
        axes[1].set_ylabel("Count")
        axes[1].set_title("Cold Snaps")

    if not extreme_precip.empty:
        axes[2].barh(
            extreme_precip["field_id"].astype(str),
            extreme_precip["n_events"],
            color="purple",
            alpha=0.7,
        )
        axes[2].set_xlabel("Number of Events")
        axes[2].set_ylabel("Field")
        axes[2].set_title("Extreme Precipitation")

    plt.tight_layout()
    plt.savefig(f"{output_dir}/extreme_events_summary.png", dpi=300, bbox_inches="tight")
    plt.close()

    print("  Saved: extreme_events_summary.png")


def run_anomaly_detection(
    weather_path: str = "output/weather_50_fields_2022_2024.csv",
    output_dir: str = "output/eda/weather",
) -> dict:
    """Run full anomaly detection pipeline."""
    print("Loading weather data...")
    df = load_weather(weather_path)
    print(f"  Loaded {len(df)} daily records")

    print("\n[1/6] Detecting Z-score anomalies...")
    zscore_anomalies = detect_zscore_anomalies(df, z_thresh=THRESHOLDS["zscore_threshold"])
    if not zscore_anomalies.empty:
        zscore_path = f"{output_dir}/zscore_anomalies.csv"
        zscore_anomalies.to_csv(zscore_path, index=False)
        print(f"  Found {len(zscore_anomalies)} Z-score anomalies")

    print("\n[2/6] Detecting heat waves...")
    heat_waves = detect_heat_waves(
        df, min_days=THRESHOLDS["heat_wave_days"], min_temp=THRESHOLDS["heat_wave_temp"]
    )
    if not heat_waves.empty:
        heat_path = f"{output_dir}/heat_waves.csv"
        heat_waves.to_csv(heat_path, index=False)
        print(f"  Found {len(heat_waves)} heat wave events")

    print("\n[3/6] Detecting cold snaps...")
    cold_snaps = detect_cold_snaps(
        df, min_days=THRESHOLDS["cold_snap_days"], max_temp=THRESHOLDS["cold_snap_temp"]
    )
    if not cold_snaps.empty:
        cold_path = f"{output_dir}/cold_snaps.csv"
        cold_snaps.to_csv(cold_path, index=False)
        print(f"  Found {len(cold_snaps)} cold snap events")

    print("\n[4/6] Detecting extreme precipitation...")
    extreme_precip = detect_extreme_precipitation(df, threshold_mm=THRESHOLDS["extreme_precip_mm"])
    if not extreme_precip.empty:
        precip_path = f"{output_dir}/extreme_precipitation.csv"
        extreme_precip.to_csv(precip_path, index=False)
        print(f"  Found {len(extreme_precip)} fields with extreme precip events")

    print("\n[5/6] Detecting drought periods...")
    droughts = detect_drought_periods(
        df, min_days=THRESHOLDS["drought_days"], max_precip_mm=THRESHOLDS["drought_precip_mm"]
    )
    if not droughts.empty:
        drought_path = f"{output_dir}/drought_periods.csv"
        droughts.to_csv(drought_path, index=False)
        print(f"  Found {len(droughts)} drought periods")

    print("\n[6/6] Creating visualizations...")
    create_anomaly_summary_plot(zscore_anomalies, f"{output_dir}/anomaly_counts.png")
    create_extreme_events_plot(heat_waves, cold_snaps, extreme_precip, output_dir)

    all_events = pd.concat(
        [
            zscore_anomalies.assign(type="zscore"),
            heat_waves.assign(type="heat_wave") if not heat_waves.empty else pd.DataFrame(),
            cold_snaps.assign(type="cold_snap") if not cold_snaps.empty else pd.DataFrame(),
        ],
        ignore_index=True,
    )

    summary = {
        "total_zscore_anomalies": len(zscore_anomalies),
        "heat_wave_events": len(heat_waves),
        "cold_snap_events": len(cold_snaps),
        "fields_with_extreme_precip": len(extreme_precip),
        "drought_periods": len(droughts),
    }

    export_json(summary, f"{output_dir}/anomaly_summary.json")
    print("  Saved: anomaly_summary.json")

    return summary


def main():
    """Run weather anomaly detection."""
    print("=" * 60)
    print("Weather Anomaly Detection")
    print("=" * 60)

    summary = run_anomaly_detection()

    print("\n" + "=" * 60)
    print("Anomaly Detection Complete")
    print("=" * 60)
    print(f"\nZ-score anomalies: {summary['total_zscore_anomalies']}")
    print(f"Heat wave events: {summary['heat_wave_events']}")
    print(f"Cold snap events: {summary['cold_snap_events']}")
    print(f"Fields with extreme precipitation: {summary['fields_with_extreme_precip']}")
    print(f"Drought periods: {summary['drought_periods']}")


if __name__ == "__main__":
    main()
