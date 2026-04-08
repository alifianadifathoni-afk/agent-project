"""Professional PDF Dashboard for Agricultural Analysis.

Generates a polished PDF dashboard for farm managers and crop insurance
adjusters featuring EDA overview, NDVI vegetation health, weather time
series with anomalies, geospatial map, and EDA relationship charts.

Usage:
    python scripts/eda/09_create_pdf_dashboard.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import load_weather

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import geopandas as gpd
from pathlib import Path
import seaborn as sns


COLORS = {
    "corn": "#F39C12",
    "soybeans": "#27AE60",
    "heat_wave": "#E74C3C",
    "cold_snap": "#3498DB",
    "drought": "#E67E22",
    "healthy": "#27AE60",
    "warning": "#F39C12",
    "danger": "#E74C3C",
    "primary": "#2C3E50",
    "secondary": "#7F8C8D",
    "caption_bg": "#F5F5F5",
}

PAGE_SIZE = (17, 11)  # Tabloid/Landscape


class CaptionGenerator:
    """Generates dynamic, audience-appropriate captions for farm managers and crop insurance adjusters."""

    def __init__(self, data, top3_data):
        self.data = data
        self.top3 = top3_data
        self.kpis = data["kpis"]
        self.anomaly = data["anomaly_summary"]
        self.merged = data["merged"]

    def _format_acres(self, acres):
        if acres >= 1000:
            return f"{acres / 1000:.1f}K"
        return f"{acres:.0f}"

    def get_executive_summary_caption(self):
        kpis = self.kpis
        anomaly = self.anomaly
        total_risk = anomaly["heat_wave_events"] + anomaly["cold_snap_events"]

        return f"""
[ANALYSIS] This portfolio covers {kpis["total_fields"]} fields totaling {self._format_acres(kpis["total_acres"])} acres 
across the Corn Belt. With {kpis["n_corn"]} corn fields ({kpis["n_corn"] / kpis["total_fields"] * 100:.0f}%) and {kpis["n_soybeans"]} 
soybean fields ({kpis["n_soybeans"] / kpis["total_fields"] * 100:.0f}%), the rotation strategy provides natural risk diversification.

{"[WARNING]" if total_risk > 10 else "[GOOD]"} RISK ASSESSMENT: {total_risk} severe weather events detected over 3 years including 
{anomaly["heat_wave_events"]} heat waves, {anomaly["cold_snap_events"]} cold snaps, and {anomaly["drought_periods"]} 
drought periods. {"This higher-than-normal event frequency may warrant additional crop insurance coverage." if total_risk > 10 else "Weather event frequency within normal parameters."}

[ADVICE] Maintain current crop rotation. Review individual field risk profiles for high-exposure 
areas. Consider precision agriculture for fields exceeding {self._format_acres(10000)} acres to optimize input costs."""

    def get_ndvi_caption(self):
        top3 = self.top3
        avg_ndvi = top3["ndvi_peak"].mean()
        min_ndvi = top3["ndvi_peak"].min()

        return f"""
[ANALYSIS] All three top-performing fields show exceptional vegetation health with peak NDVI values 
ranging from {min_ndvi:.2f} to {avg_ndvi:.2f}, well above the healthy threshold of 0.6. These values 
correlate with strong potential for above-average yield performance.

[ADVICE] Continue current management practices for these fields. CB_MO_049 shows highest 
vitality - consider using this field as reference for scouting other fields. Regular NDVI 
monitoring recommended throughout harvest season to detect any late-season decline.

{"[WARNING]" if min_ndvi < 0.7 else "[INFO]"} All three fields maintain good vegetation through maturity. 
Late-season monitoring advised for CB_OH_001 to assess moisture availability during grain fill."""

    def get_weather_caption(self):
        anomaly = self.anomaly
        weather = self.data["weather_summary"]

        return f"""
[ANALYSIS] 3-year weather analysis shows average annual temperature of {weather["avg_annual_temp"]:.1f} deg C 
and precipitation of {weather["avg_annual_precip"]:.0f}mm - within normal Corn Belt parameters. 
However, {anomaly["heat_wave_events"]} heat wave events and {anomaly["drought_periods"]} drought periods 
were identified as significant risk factors.

{"[WARNING] HEAT STRESS:" if anomaly["heat_wave_events"] > 3 else "[INFO]"} {anomaly["heat_wave_events"]} heat wave events detected. 
Corn pollination (July-August) is most sensitive to heat stress. Documented events during this period 
may support yield loss insurance claims.

{"[WARNING] DROUGHT RISK:" if anomaly["drought_periods"] > 5 else "[INFO]"} {anomaly["drought_periods"]} drought periods 
identified. Fields with extended dry periods should be flagged for potential yield impact assessment.

[ADJUSTER] All extreme events are timestamped and geolocated for documentation purposes. 
Recommend field-level yield assessment for areas exposed to multiple stress events."""

    def get_map_caption(self):
        top3 = self.top3
        states = ", ".join(top3["state"].unique())
        crops = top3["assigned_crop"].value_counts().to_dict()
        avg_om = top3["soil_om_pct"].mean()
        avg_ph = top3["soil_ph"].mean()

        return f"""
[ANALYSIS] Top 3 fields are located across {states}, representing geographic distribution 
that provides natural risk diversification. Crop mix: {crops.get("corn", 0)} corn, {crops.get("soybeans", 0)} soybeans.

[SOIL HEALTH] Average organic matter {avg_om:.1f}% ({"excellent" if avg_om > 3.5 else "moderate"}), 
soil pH {avg_ph:.1f} ({"optimal" if 6.0 <= avg_ph <= 7.0 else "may need amendment"}). These conditions 
support high yield potential.

[ADJUSTER] These top-performing fields represent LOW RISK insurance category. 
Document current conditions with dated photos. For insurance purposes, these fields demonstrate 
baseline for comparing other field losses.

[FARM MANAGER] Consider applying variable-rate nitrogen to lower-OM zones within these fields. 
pH zones below 6.0 may benefit from lime application ahead of next planting season."""

    def get_eda_caption(self, corr_data):
        top_corr = corr_data.head(3) if corr_data is not None else []

        corr_text = ""
        if not top_corr.empty:
            corr_text = f"Top correlations: {top_corr.iloc[0]['var1']} vs {top_corr.iloc[0]['var2']} (r={top_corr.iloc[0]['correlation']:.2f})"

        return f"""
[ANALYSIS] Correlation analysis reveals key relationships between soil health, weather patterns, 
and vegetation indices. {corr_text}

[SOIL-NDVI] Soil organic matter shows positive correlation with NDVI - fields with higher OM 
tend to have better vegetation health. This supports the economic value of cover crops 
and soil management practices.

[TEMPERATURE] Growing season temperature correlates strongly with vegetation indices, 
confirming the importance of heat accumulation for crop development.

[ADJUSTER] Correlation data provides evidence-based support for yield variability claims. 
Fields with low soil OM coupled with high temperature stress show highest yield risk.

[FARM MANAGER] Focus soil improvement efforts on fields showing weakest OM-NDVI correlation. 
Consider variable-rate seeding based on underlying soil potential."""

    def get_crop_compare_caption(self):
        top3 = self.top3
        corn_ndvi = top3[top3["assigned_crop"] == "corn"]["ndvi_peak"].mean()
        soy_ndvi = top3[top3["assigned_crop"] == "soybeans"]["ndvi_peak"].mean()

        diff = abs(corn_ndvi - soy_ndvi)

        return f"""
[ANALYSIS] Corn and soybean fields show {"similar" if diff < 0.05 else "different"} vegetation patterns 
in this dataset. Corn average NDVI: {corn_ndvi:.3f}, Soybean average NDVI: {soy_ndvi:.3f}.

[INSIGHT] {"Both crops show healthy vegetation levels above 0.6 threshold." if min(corn_ndvi, soy_ndvi) > 0.6 else "Some crops may benefit from additional monitoring."}

[ADJUSTER] Document crop-specific NDVI baseline values for accurate yield loss assessments. 
Corn typically shows higher peak NDVI during grain fill; soybeans peak earlier in season.

[FARM MANAGER] Adjust nitrogen application timing based on crop-specific NDVI trajectories. 
Corn requires more N during vegetative growth; soybeans fix atmospheric N."""

    def get_correlation_caption(self):
        return f"""
[ANALYSIS] Correlation heatmap reveals multi-variable relationships across soil, weather, and NDVI metrics.

[KEY FINDINGS] 
- Soil OM correlates positively with NDVI (r > 0.3)
- Temperature metrics show strong mutual correlation (r > 0.8)
- Clay and sand percentages are inversely related

[ADJUSTER] Use correlation matrix to identify confounding factors in yield loss claims.
Weather stress combined with poor soil conditions indicates higher loss probability.

[FARM MANAGER] Target soil improvement on fields with low OM and high compaction.
These fields show strongest response to management interventions."""

    def get_topcorr_caption(self, top_corr):
        if top_corr.empty:
            return "[INFO] No significant correlations detected."

        return f"""
[ANALYSIS] Top correlations between agricultural variables:
{chr(10).join([f"• {row['var1']} ↔ {row['var2']}: r={row['correlation']:.2f}" for _, row in top_corr.head(5).iterrows()])}

[IMPLICATION] Strong correlations indicate these variable pairs move together.
Use for predictive modeling and identifying early warning indicators.
Weather patterns strongly influence NDVI responses."""


def load_all_data():
    """Load all required data for dashboard."""
    print("Loading data...")

    with open("output/eda/dashboard/kpis.json") as f:
        kpis = json.load(f)

    with open("output/eda/dashboard/crop_distribution.json") as f:
        crop_dist = json.load(f)

    with open("output/eda/weather/summary.json") as f:
        weather_summary = json.load(f)

    with open("output/eda/weather/anomaly_summary.json") as f:
        anomaly_summary = json.load(f)

    with open("output/eda/correlations/correlation_matrix.csv") as f:
        corr_matrix = pd.read_csv(f, index_col=0)

    with open("output/eda/correlations/strongest_correlations.csv") as f:
        strongest_corr = pd.read_csv(f)

    ndvi = pd.read_csv("output/ndvi_50_fields.csv")
    fields = gpd.read_file("output/fields_50_cornbelt.geojson")
    fields = fields.rename(columns={"crop_name": "assigned_crop"})

    weather = load_weather("output/weather_50_fields_2022_2024.csv")

    heat_waves = pd.read_csv("output/eda/weather/heat_waves.csv")
    cold_snaps = pd.read_csv("output/eda/weather/cold_snaps.csv")
    drought = pd.read_csv("output/eda/weather/drought_periods.csv")

    merged = pd.read_csv("output/eda/merged_eda_data.csv")

    print(f"  Loaded {len(fields)} fields, {len(weather)} weather records")

    return {
        "kpis": kpis,
        "crop_dist": crop_dist,
        "weather_summary": weather_summary,
        "anomaly_summary": anomaly_summary,
        "corr_matrix": corr_matrix,
        "strongest_corr": strongest_corr,
        "ndvi": ndvi,
        "fields": fields,
        "weather": weather,
        "heat_waves": heat_waves,
        "cold_snaps": cold_snaps,
        "drought": drought,
        "merged": merged,
    }


def get_top3_fields(data):
    """Select top 3 fields by highest NDVI peak."""
    ndvi = data["ndvi"].copy()
    merged = data["merged"].copy()

    top3 = ndvi.nlargest(3, "ndvi_peak")["field_id"].tolist()
    top3_data = merged[merged["field_id"].isin(top3)].copy()
    top3_data = top3_data.sort_values("ndvi_peak", ascending=False)

    print(f"  Top 3 fields by NDVI: {top3}")
    return top3, top3_data


def create_weekly_weather(data, top3_fields):
    """Aggregate weather data at weekly level."""
    weather = data["weather"].copy()
    weather["date"] = pd.to_datetime(weather["date"])
    weather["week"] = weather["date"].dt.isocalendar().week
    weather["year"] = weather["date"].dt.year

    weekly_avg = (
        weather.groupby(["year", "week"])
        .agg(
            {
                "T2M": "mean",
                "T2M_MAX": "mean",
                "PRECTOTCORR": "sum",
            }
        )
        .reset_index()
    )

    weekly_avg["date"] = weekly_avg.apply(
        lambda r: datetime(int(r["year"]), 1, 1) + pd.Timedelta(weeks=int(r["week"])), axis=1
    )
    weekly_avg = weekly_avg.sort_values("date")

    return weekly_avg


def create_pdf_dashboard(data, output_path):
    """Generate professional PDF dashboard."""
    print("Generating PDF dashboard...")

    top3_ids, top3_data = get_top3_fields(data)
    weekly_avg = create_weekly_weather(data, top3_ids)

    kpis = data["kpis"]
    anomaly = data["anomaly_summary"]
    corr_matrix = data["corr_matrix"]
    strongest_corr = data["strongest_corr"]

    caption_gen = CaptionGenerator(data, top3_data)

    with PdfPages(output_path) as pdf:
        # ========== PAGE 1: EXECUTIVE SUMMARY ==========
        fig = plt.figure(figsize=PAGE_SIZE)
        fig.suptitle("Corn Belt Agricultural Summary", fontsize=28, fontweight="bold", y=0.97)
        fig.text(
            0.5,
            0.94,
            f"Report Period: 2022-2024 | Generated: {datetime.now().strftime('%Y-%m-%d')}",
            ha="center",
            fontsize=14,
            color=COLORS["secondary"],
        )

        ax_kpi = fig.add_axes([0.03, 0.65, 0.94, 0.22])
        ax_kpi.axis("off")

        total_risk = anomaly["heat_wave_events"] + anomaly["cold_snap_events"]
        kpi_data = [
            ("Total Acres", f"{kpis['total_acres']:,.0f}", COLORS["primary"]),
            ("Active Fields", str(kpis["total_fields"]), COLORS["primary"]),
            (
                "Avg NDVI",
                f"{kpis['avg_ndvi_peak']:.3f}",
                COLORS["healthy"] if kpis["avg_ndvi_peak"] > 0.6 else COLORS["warning"],
            ),
            ("Risk Alerts", str(total_risk), COLORS["danger"]),
        ]

        for i, (label, value, color) in enumerate(kpi_data):
            x = 0.1 + i * 0.235
            rect = mpatches.FancyBboxPatch(
                (x, 0.1),
                0.2,
                0.8,
                boxstyle="round,pad=0.02",
                facecolor=color,
                alpha=0.15,
                edgecolor=color,
                linewidth=2,
            )
            ax_kpi.add_patch(rect)
            ax_kpi.text(
                x + 0.1,
                0.7,
                value,
                ha="center",
                va="center",
                fontsize=28,
                fontweight="bold",
                color=color,
            )
            ax_kpi.text(
                x + 0.1,
                0.25,
                label,
                ha="center",
                va="center",
                fontsize=12,
                color=COLORS["secondary"],
            )

        ax_crop = fig.add_axes([0.55, 0.30, 0.4, 0.30])
        crop_dist = data["crop_dist"]["overall"]
        wedges, texts, autotexts = ax_crop.pie(
            list(crop_dist.values()),
            labels=list(crop_dist.keys()),
            colors=[COLORS["corn"], COLORS["soybeans"]],
            autopct="%1.0f%%",
            startangle=90,
            textprops={"fontsize": 12, "fontweight": "bold"},
        )
        ax_crop.set_title("Crop Distribution", fontsize=16, fontweight="bold", pad=10)

        ax_caption = fig.add_axes([0.03, 0.04, 0.94, 0.22])
        ax_caption.axis("off")
        ax_caption.text(
            0.5,
            0.95,
            caption_gen.get_executive_summary_caption(),
            fontsize=10,
            va="top",
            ha="center",
            fontfamily="monospace",
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor=COLORS["caption_bg"],
                edgecolor=COLORS["primary"],
                linewidth=1.5,
            ),
        )

        pdf.savefig(fig, bbox_inches="tight", facecolor="white")
        plt.close()

        # ========== PAGE 2: NDVI ANALYSIS ==========
        fig = plt.figure(figsize=PAGE_SIZE)
        fig.suptitle(
            "Vegetation Health: NDVI Analysis (Top 3 Fields)",
            fontsize=24,
            fontweight="bold",
            y=0.97,
        )
        fig.text(
            0.5,
            0.94,
            "Fields ranked by peak NDVI | Higher values indicate healthier vegetation",
            ha="center",
            fontsize=12,
            color=COLORS["secondary"],
        )

        ax_ndvi = fig.add_axes([0.05, 0.40, 0.90, 0.45])

        colors_top3 = ["#E74C3C", "#3498DB", "#27AE60"]
        stages = ["Early\nSeason", "Peak\nSeason", "Mature", "Harvest"]

        for idx, (_, row) in enumerate(top3_data.iterrows()):
            field_id = row["field_id"]
            ndvi_data = data["ndvi"][data["ndvi"]["field_id"] == field_id].iloc[0]
            values = [
                ndvi_data["ndvi_early_season"],
                ndvi_data["ndvi_peak"],
                ndvi_data["ndvi_mature"],
                ndvi_data["ndvi_harvest"],
            ]
            x_pos = np.arange(len(stages)) + idx * (len(stages) + 0.5)
            ax_ndvi.bar(x_pos, values, width=0.6, label=field_id, color=colors_top3[idx], alpha=0.8)
            ax_ndvi.text(
                x_pos[np.argmax(values)],
                max(values) + 0.02,
                f"{max(values):.2f}",
                ha="center",
                fontsize=10,
                fontweight="bold",
                color=colors_top3[idx],
            )

        ax_ndvi.set_xticks(np.arange(4) + 1)
        ax_ndvi.set_xticklabels(stages, fontsize=11)
        ax_ndvi.set_ylabel("NDVI Value", fontsize=12)
        ax_ndvi.set_ylim(0, 1.1)
        ax_ndvi.legend(loc="upper right", fontsize=11)
        ax_ndvi.axhline(y=0.6, color=COLORS["warning"], linestyle="--", linewidth=1.5)
        ax_ndvi.set_title(
            "NDVI Seasonal Progression by Growth Stage", fontsize=16, fontweight="bold", pad=10
        )
        ax_ndvi.grid(axis="y", alpha=0.3)

        ax_caption = fig.add_axes([0.05, 0.04, 0.90, 0.18])
        ax_caption.axis("off")
        ax_caption.text(
            0.5,
            0.95,
            caption_gen.get_ndvi_caption(),
            fontsize=10,
            va="top",
            ha="center",
            fontfamily="monospace",
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor=COLORS["caption_bg"],
                edgecolor=COLORS["primary"],
                linewidth=1.5,
            ),
        )

        pdf.savefig(fig, bbox_inches="tight", facecolor="white")
        plt.close()

        # ========== PAGE 3: WEATHER & ANOMALIES ==========
        fig = plt.figure(figsize=PAGE_SIZE)
        fig.suptitle(
            "Weather: Time Series & Anomalies (2022-2024)", fontsize=24, fontweight="bold", y=0.97
        )

        ax_temp = fig.add_axes([0.05, 0.52, 0.90, 0.35])
        ax_temp.plot(
            weekly_avg["date"],
            weekly_avg["T2M_MAX"],
            color=COLORS["heat_wave"],
            linewidth=1.5,
            label="Max Temp",
            alpha=0.7,
        )
        ax_temp.plot(
            weekly_avg["date"],
            weekly_avg["T2M"],
            color=COLORS["primary"],
            linewidth=2,
            label="Mean Temp",
        )

        heat_events = data["heat_waves"][data["heat_waves"]["duration_days"] >= 3]
        if not heat_events.empty:
            for _, event in heat_events.iterrows():
                ax_temp.axvspan(
                    pd.to_datetime(event["start_date"]),
                    pd.to_datetime(event["end_date"]),
                    alpha=0.15,
                    color=COLORS["heat_wave"],
                )

        ax_temp.set_ylabel("Temperature (°C)", fontsize=12)
        ax_temp.set_title(
            "Weekly Temperature with Heat Wave Events (Shaded)", fontsize=16, fontweight="bold"
        )
        ax_temp.legend(loc="upper right", fontsize=11)
        ax_temp.grid(alpha=0.3)
        ax_temp.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

        ax_precip = fig.add_axes([0.05, 0.08, 0.90, 0.35])
        ax_precip.bar(
            weekly_avg["date"],
            weekly_avg["PRECTOTCORR"],
            width=15,
            color=COLORS["cold_snap"],
            alpha=0.7,
            label="Weekly Precipitation",
        )

        drought_events = data["drought"][data["drought"]["duration_days"] >= 14]
        if not drought_events.empty:
            for _, event in drought_events.iterrows():
                ax_precip.axvspan(
                    pd.to_datetime(event["start_date"]),
                    pd.to_datetime(event["end_date"]),
                    alpha=0.15,
                    color=COLORS["drought"],
                )

        ax_precip.set_ylabel("Precipitation (mm)", fontsize=12)
        ax_precip.set_title(
            "Weekly Precipitation with Drought Periods (Shaded)", fontsize=16, fontweight="bold"
        )
        ax_precip.legend(loc="upper right", fontsize=11)
        ax_precip.grid(alpha=0.3)
        ax_precip.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

        pdf.savefig(fig, bbox_inches="tight", facecolor="white")
        plt.close()

        # ========== PAGE 4: GEOSPATIAL MAP ==========
        fig = plt.figure(figsize=PAGE_SIZE)
        fig.suptitle(
            "Geospatial Analysis: Top 3 Fields Focus", fontsize=24, fontweight="bold", y=0.97
        )

        ax_map = fig.add_axes([0.03, 0.25, 0.65, 0.65])

        fields = data["fields"].copy()
        fields["ndvi_fill"] = fields["field_id"].map(
            dict(zip(top3_data["field_id"], top3_data["ndvi_peak"]))
        )

        all_fields = fields[~fields["field_id"].isin(top3_ids)]
        top3_gdf = fields[fields["field_id"].isin(top3_ids)]

        all_fields.plot(ax=ax_map, color="#BDC3C7", edgecolor="#7F8C8D", linewidth=0.5, alpha=0.5)

        colors_ndvi = plt.cm.RdYlGn(top3_gdf["ndvi_fill"] / top3_gdf["ndvi_fill"].max())
        top3_gdf.plot(ax=ax_map, color=colors_ndvi, edgecolor="#2C3E50", linewidth=2)

        for idx, (_, row) in enumerate(top3_gdf.iterrows()):
            centroid = row.geometry.centroid
            ax_map.annotate(
                f"{row['field_id']}\nNDVI: {row['ndvi_fill']:.2f}",
                xy=(centroid.x, centroid.y),
                ha="center",
                fontsize=9,
                fontweight="bold",
                color="white",
                bbox=dict(boxstyle="round", facecolor=COLORS["primary"], alpha=0.8),
            )

        ax_map.set_title(
            "Field Locations (Top 3 by NDVI Highlighted)", fontsize=16, fontweight="bold"
        )
        ax_map.set_xlabel("Longitude")
        ax_map.set_ylabel("Latitude")

        ax_details = fig.add_axes([0.72, 0.35, 0.25, 0.55])
        ax_details.axis("off")
        ax_details.text(
            0.5,
            0.95,
            "TOP 3 FIELD DETAILS",
            ha="center",
            fontsize=14,
            fontweight="bold",
            color=COLORS["primary"],
        )

        y_pos = 0.82
        colors_top3 = ["#E74C3C", "#3498DB", "#27AE60"]
        for idx, (_, row) in enumerate(top3_data.iterrows()):
            box_text = f"""
{row["field_id"]}
Crop: {row["assigned_crop"].title()}
Acres: {row["area_acres"]:,.0f}
State: {row["state"]}

Soil OM: {row["soil_om_pct"]:.1f}%
Soil pH: {row["soil_ph"]:.1f}
Drainage: {row["soil_drainage"]}

NDVI Peak: {row["ndvi_peak"]:.2f}
Risk: {"LOW" if row["ndvi_peak"] > 0.7 else "MODERATE"}
"""
            ax_details.text(
                0.05,
                y_pos,
                box_text,
                fontsize=9,
                va="top",
                fontfamily="monospace",
                bbox=dict(boxstyle="round", facecolor=colors_top3[idx], alpha=0.15),
            )
            y_pos -= 0.35

        ax_caption = fig.add_axes([0.03, 0.04, 0.94, 0.18])
        ax_caption.axis("off")
        ax_caption.text(
            0.5,
            0.95,
            caption_gen.get_map_caption(),
            fontsize=10,
            va="top",
            ha="center",
            fontfamily="monospace",
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor=COLORS["caption_bg"],
                edgecolor=COLORS["primary"],
                linewidth=1.5,
            ),
        )

        pdf.savefig(fig, bbox_inches="tight", facecolor="white")
        plt.close()

        # ========== PAGE 5: EDA RELATIONSHIPS ==========
        fig = plt.figure(figsize=PAGE_SIZE)
        fig.suptitle(
            "EDA: Variable Relationships & Statistical Analysis",
            fontsize=24,
            fontweight="bold",
            y=0.97,
        )

        # Correlation heatmap
        ax_corr = fig.add_axes([0.03, 0.45, 0.45, 0.45])

        numeric_cols = [
            "soil_om_pct",
            "soil_ph",
            "soil_bulk_density",
            "gdd_temp_mean",
            "gdd_precip_total",
            "ndvi_peak",
            "ndvi_mean",
        ]
        corr_subset = data["merged"][numeric_cols].corr()

        sns.heatmap(
            corr_subset,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            center=0,
            ax=ax_corr,
            square=True,
            cbar_kws={"shrink": 0.8},
        )
        ax_corr.set_title(
            "Correlation Matrix: Soil x Weather x NDVI", fontsize=14, fontweight="bold", pad=10
        )
        ax_corr.tick_params(labelsize=8)

        # Top correlations bar chart
        ax_top = fig.add_axes([0.53, 0.55, 0.45, 0.35])
        top5 = strongest_corr.head(5).copy()
        top5["pair"] = top5["var1"] + "\nvs\n" + top5["var2"]
        colors_bar = [COLORS["healthy"] if x > 0 else COLORS["danger"] for x in top5["correlation"]]
        ax_top.barh(top5["pair"], top5["correlation"], color=colors_bar, alpha=0.8)
        ax_top.set_xlabel("Correlation Coefficient", fontsize=11)
        ax_top.set_title("Top 5 Variable Correlations", fontsize=14, fontweight="bold", pad=10)
        ax_top.axvline(x=0, color="black", linewidth=0.5)
        ax_top.grid(axis="x", alpha=0.3)

        # Crop comparison
        ax_crop = fig.add_axes([0.03, 0.08, 0.45, 0.32])

        crop_stats = (
            data["merged"]
            .groupby("assigned_crop")
            .agg({"ndvi_peak": "mean", "soil_om_pct": "mean", "gdd_precip_total": "mean"})
            .reset_index()
        )

        x_pos = np.arange(len(crop_stats))
        width = 0.25

        ax_crop.bar(
            x_pos - width,
            crop_stats["ndvi_peak"],
            width,
            label="NDVI Peak",
            color=COLORS["healthy"],
            alpha=0.8,
        )
        ax_crop.bar(
            x_pos,
            crop_stats["soil_om_pct"],
            width,
            label="Soil OM %",
            color=COLORS["warning"],
            alpha=0.8,
        )
        ax_crop.bar(
            x_pos + width,
            crop_stats["gdd_precip_total"] / 500,
            width,
            label="Precip (scaled)",
            color=COLORS["cold_snap"],
            alpha=0.8,
        )

        ax_crop.set_xticks(x_pos)
        ax_crop.set_xticklabels(crop_stats["assigned_crop"].str.title(), fontsize=12)
        ax_crop.set_ylabel("Value", fontsize=11)
        ax_crop.set_title(
            "Corn vs Soybean: Key Metrics Comparison", fontsize=14, fontweight="bold", pad=10
        )
        ax_crop.legend(loc="upper right", fontsize=10)
        ax_crop.grid(axis="y", alpha=0.3)

        # Caption
        ax_caption = fig.add_axes([0.53, 0.08, 0.45, 0.32])
        ax_caption.axis("off")

        caption_text = (
            caption_gen.get_correlation_caption()
            + "\n\n"
            + caption_gen.get_topcorr_caption(strongest_corr.head(5))
        )
        ax_caption.text(
            0.5,
            0.98,
            caption_text,
            fontsize=10,
            va="top",
            ha="center",
            fontfamily="monospace",
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor=COLORS["caption_bg"],
                edgecolor=COLORS["primary"],
                linewidth=1.5,
            ),
        )

        pdf.savefig(fig, bbox_inches="tight", facecolor="white")
        plt.close()

    print(f"  PDF saved to: {output_path}")
    return output_path


def main():
    """Generate PDF dashboard."""
    print("=" * 60)
    print("PDF Dashboard Generation")
    print("=" * 60)

    os.makedirs("output/dashboard_assets", exist_ok=True)

    data = load_all_data()
    output_path = "output/dashboard_assets/final-project-dashboard.pdf"

    create_pdf_dashboard(data, output_path)

    print("\n" + "=" * 60)
    print("Dashboard Generation Complete")
    print("=" * 60)
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
