"""Create visualizations for Illinois Corn Belt soil analysis.

Creates:
- output/soil_om_choropleth.png
- output/workflow_figure.png
- output/soil_properties_analysis.png

Usage:
    python scripts/visualize_illinois_soil.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

sys.path.insert(0, str(PROJECT_ROOT / ".opencode" / "skills" / "ssurgo-soil" / "src"))

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from ssurgo_soil import get_soil_at_point
from ssurgo_workflows import (
    prepare_ssurgo_field_package,
    render_ssurgo_property_map,
    render_complete_workflow_figure,
)


def create_property_distributions(soil: pd.DataFrame, field_id: str) -> None:
    """Create distribution plots for soil properties."""
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    fig.suptitle(f"Soil Properties - Field {field_id}", fontsize=14, fontweight="bold")

    ax = axes[0, 0]
    soil["om_r"].hist(bins=15, ax=ax, color="steelblue", edgecolor="black", alpha=0.7)
    ax.set_xlabel("Organic Matter (%)")
    ax.set_ylabel("Frequency")
    ax.set_title("Organic Matter Distribution")

    ax = axes[0, 1]
    soil["ph1to1h2o_r"].hist(bins=15, ax=ax, color="forestgreen", edgecolor="black", alpha=0.7)
    ax.set_xlabel("pH")
    ax.set_ylabel("Frequency")
    ax.set_title("pH Distribution")

    ax = axes[0, 2]
    soil["claytotal_r"].hist(bins=15, ax=ax, color="sienna", edgecolor="black", alpha=0.7)
    ax.set_xlabel("Clay (%)")
    ax.set_ylabel("Frequency")
    ax.set_title("Clay Content Distribution")

    ax = axes[1, 0]
    drainage_cats = soil.groupby("compname")["om_r"].mean().reset_index()
    drainage_cats.columns = ["Soil Series", "OM %"]
    drainage_cats.plot(
        kind="bar",
        x="Soil Series",
        y="OM %",
        ax=ax,
        color=["steelblue", "coral"][: len(drainage_cats)],
        alpha=0.7,
    )
    ax.set_title("OM by Soil Series")
    ax.set_ylabel("Organic Matter (%)")
    ax.tick_params(axis="x", rotation=45)

    ax = axes[1, 1]
    avg_texture = {
        "Clay": soil["claytotal_r"].mean(),
        "Sand": soil["sandtotal_r"].mean(),
        "Silt": soil["silttotal_r"].mean(),
    }
    ax.bar(
        avg_texture.keys(),
        avg_texture.values(),
        color=["sienna", "gold", "gray"],
        alpha=0.7,
        edgecolor="black",
    )
    ax.set_title("Average Soil Texture")
    ax.set_ylabel("Percentage (%)")

    ax = axes[1, 2]
    ax.axis("off")
    dominant = soil.sort_values(["comppct_r", "hzdept_r"], ascending=[False, True]).iloc[0]
    summary_text = f"""SOIL SUMMARY
━━━━━━━━━━━━━━━━━━
Location: Illinois Corn Belt
Field ID: {field_id}

Dominant Soil: {dominant["compname"]}
Map Unit: {dominant["muname"][:40]}

Drainage: {dominant["drainagecl"]}
Organic Matter: {dominant["om_r"]:.1f}%
pH: {dominant["ph1to1h2o_r"]:.1f}
Clay: {dominant["claytotal_r"]:.0f}%
Sand: {dominant["sandtotal_r"]:.0f}%
Silt: {dominant["silttotal_r"]:.0f}%

Bulk Density: {dominant["dbthirdbar_r"]:.2f} g/cm³
CEC: {dominant["cec7_r"]:.1f} meq/100g
AWC: {dominant["awc_r"]:.2f} in/in"""
    ax.text(
        0.1,
        0.95,
        summary_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        fontfamily="monospace",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "soil_properties_analysis.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {OUTPUT_DIR / 'soil_properties_analysis.png'}")


def main():
    print("Loading field and soil data...")

    fields = gpd.read_file(DATA_DIR / "field_illinois_corn.geojson")
    field = fields.to_crs("EPSG:4326")
    field_id = field["field_id"].iloc[0]

    soil = pd.read_csv(DATA_DIR / "soil_illinois_corn.csv")
    print(f"  Loaded {len(soil)} soil records for field {field_id}")

    print("\nPreparing SSURGO field package...")
    try:
        ssurgo_polys, detail_table, agg = prepare_ssurgo_field_package(
            field, field_id_column="field_id", max_depth_cm=30
        )
        print(f"  SSURGO polygons: {len(ssurgo_polys)}")
    except Exception as e:
        print(f"  Note: {e}")
        ssurgo_polys = gpd.GeoDataFrame()
        detail_table = pd.DataFrame()

    print("\n=== Creating Visualizations ===")

    print("Creating OM choropleth...")
    try:
        if not ssurgo_polys.empty and "om_r" in ssurgo_polys.columns:
            render_ssurgo_property_map(
                field,
                ssurgo_polys,
                "om_r",
                str(OUTPUT_DIR / "soil_om_choropleth.png"),
                title="Organic Matter % (Natural Breaks)",
                show_axis_labels=False,
            )
            print(f"  Saved: {OUTPUT_DIR / 'soil_om_choropleth.png'}")
    except Exception as e:
        print(f"  Choropleth skipped: {e}")

    print("Creating workflow figure...")
    try:
        if not ssurgo_polys.empty and not detail_table.empty:
            render_complete_workflow_figure(
                field,
                ssurgo_polys,
                detail_table,
                str(OUTPUT_DIR / "workflow_figure.png"),
                combine_width_m=9.0,
            )
            print(f"  Saved: {OUTPUT_DIR / 'workflow_figure.png'}")
    except Exception as e:
        print(f"  Workflow figure skipped: {e}")

    print("Creating property distributions...")
    create_property_distributions(soil, field_id)

    print("\n✓ All visualizations complete!")


if __name__ == "__main__":
    main()
