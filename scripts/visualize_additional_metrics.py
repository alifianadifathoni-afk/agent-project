#!/usr/bin/env python3
"""Additional soil metric visualizations.

Creates multiple plots:
- pH distribution by drainage class (box plot)
- CEC comparison: Top 10 vs Bottom 10 (box plot)
- Carbon storage by drainage class (bar chart)
- Soil health score by drainage class (bar chart)
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import geopandas as gpd

# Set style
plt.style.use("seaborn-v0_8-whitegrid")
sns.set_palette("husl")

# Load data
df = pd.read_csv("data/soil_erosion_carbon_analysis.csv")

# =============================================================================
# Plot 1: pH Distribution by Drainage Class
# =============================================================================
fig1, ax1 = plt.subplots(figsize=(10, 6))

# Order drainage classes by typical wetness (driest first)
drainage_order = [
    "Well drained",
    "Moderately well drained",
    "Somewhat poorly drained",
    "Poorly drained",
]

# Box plot
palette_drainage = {
    "Well drained": "#27ae60",
    "Moderately well drained": "#f39c12",
    "Somewhat poorly drained": "#1abc9c",
    "Poorly drained": "#3498db",
}

sns.boxplot(
    data=df, x="drainage_class", y="ph_avg", order=drainage_order, palette=palette_drainage, ax=ax1
)
sns.stripplot(
    data=df,
    x="drainage_class",
    y="ph_avg",
    order=drainage_order,
    color="black",
    alpha=0.6,
    size=6,
    ax=ax1,
)

ax1.set_title("pH Distribution by Drainage Class", fontsize=14, fontweight="bold")
ax1.set_xlabel("Drainage Class", fontsize=12)
ax1.set_ylabel("pH (average)", fontsize=12)
ax1.axhline(y=6.5, color="red", linestyle="--", alpha=0.5, label="Ideal pH (6.5)")
ax1.axhline(y=7.0, color="orange", linestyle="--", alpha=0.5, label="Neutral (7.0)")
ax1.legend(loc="lower right")

plt.tight_layout()
plt.savefig("data/ph_distribution.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print("✓ Created: data/ph_distribution.png")

# =============================================================================
# Plot 2: CEC Comparison - Top 10 vs Bottom 10
# =============================================================================
fig2, ax2 = plt.subplots(figsize=(9, 6))

top_10 = df.nsmallest(10, "rank").copy()
bottom_10 = df.nlargest(10, "rank").copy()

top_10["group"] = "Top 10\n(High Productivity)"
bottom_10["group"] = "Bottom 10\n(Low Productivity)"
combined = pd.concat([top_10, bottom_10])

palette_cec = {"Top 10\n(High Productivity)": "#3498db", "Bottom 10\n(Low Productivity)": "#e74c3c"}

sns.boxplot(data=combined, x="group", y="cec_avg", palette=palette_cec, ax=ax2)
sns.stripplot(data=combined, x="group", y="cec_avg", color="black", alpha=0.7, size=8, ax=ax2)

# Add field labels
for i, (idx, row) in enumerate(combined.iterrows()):
    group_idx = 0 if row["group"].startswith("Top") else 1
    ax2.annotate(
        row["field_id"],
        xy=(group_idx, row["cec_avg"]),
        xytext=(5, 3),
        textcoords="offset points",
        fontsize=7,
        alpha=0.8,
    )

ax2.set_title("Cation Exchange Capacity (CEC): Top 10 vs Bottom 10", fontsize=14, fontweight="bold")
ax2.set_ylabel("CEC (meq/100g)", fontsize=12)
ax2.set_xlabel("")

# Stats
top_cec = top_10["cec_avg"].mean()
bottom_cec = bottom_10["cec_avg"].mean()
ax2.text(
    0.98,
    0.02,
    f"Top 10 mean: {top_cec:.1f}\nBottom 10 mean: {bottom_cec:.1f}",
    transform=ax2.transAxes,
    fontsize=10,
    va="bottom",
    ha="right",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
)

plt.tight_layout()
plt.savefig("data/cec_comparison.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print("✓ Created: data/cec_comparison.png")

# =============================================================================
# Plot 3: Carbon Storage by Drainage Class
# =============================================================================
fig3, ax3 = plt.subplots(figsize=(10, 6))

# Group by drainage and calculate mean
carbon_by_drainage = (
    df.groupby("drainage_class")["carbon_storage_mg_ha"]
    .agg(["mean", "std"])
    .reindex(drainage_order)
)

colors = [palette_drainage[d] for d in drainage_order]
bars = ax3.bar(
    range(len(drainage_order)),
    carbon_by_drainage["mean"],
    color=colors,
    edgecolor="black",
    alpha=0.8,
    yerr=carbon_by_drainage["std"],
    capsize=5,
)

ax3.set_xticks(range(len(drainage_order)))
ax3.set_xticklabels(drainage_order, rotation=15, ha="right")
ax3.set_title("Carbon Storage Potential by Drainage Class", fontsize=14, fontweight="bold")
ax3.set_ylabel("Carbon Storage (Mg/ha)", fontsize=12)
ax3.set_xlabel("Drainage Class", fontsize=12)

# Add value labels on bars
for bar, val in zip(bars, carbon_by_drainage["mean"]):
    ax3.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 1,
        f"{val:.1f}",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
    )

plt.tight_layout()
plt.savefig("data/carbon_by_drainage.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print("✓ Created: data/carbon_by_drainage.png")

# =============================================================================
# Plot 4: Soil Health Score by Drainage Class
# =============================================================================
fig4, ax4 = plt.subplots(figsize=(10, 6))

health_by_drainage = (
    df.groupby("drainage_class")["soil_health_score"].agg(["mean", "std"]).reindex(drainage_order)
)

bars = ax4.bar(
    range(len(drainage_order)),
    health_by_drainage["mean"],
    color=colors,
    edgecolor="black",
    alpha=0.8,
    yerr=health_by_drainage["std"],
    capsize=5,
)

ax4.set_xticks(range(len(drainage_order)))
ax4.set_xticklabels(drainage_order, rotation=15, ha="right")
ax4.set_title("Soil Health Score by Drainage Class", fontsize=14, fontweight="bold")
ax4.set_ylabel("Soil Health Score (0-100)", fontsize=12)
ax4.set_xlabel("Drainage Class", fontsize=12)
ax4.set_ylim(0, 100)

# Add value labels
for bar, val in zip(bars, health_by_drainage["mean"]):
    ax4.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 2,
        f"{val:.1f}",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
    )

plt.tight_layout()
plt.savefig("data/health_by_drainage.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print("✓ Created: data/health_by_drainage.png")

# =============================================================================
# Summary Statistics
# =============================================================================
print("\n" + "=" * 60)
print("SUMMARY STATISTICS")
print("=" * 60)

print("\n--- pH by Drainage Class ---")
for dc in drainage_order:
    subset = df[df["drainage_class"] == dc]
    print(f"  {dc}: mean={subset['ph_avg'].mean():.2f}, n={len(subset)}")

print(f"\n--- CEC Comparison ---")
print(f"  Top 10: mean={top_cec:.1f} meq/100g")
print(f"  Bottom 10: mean={bottom_cec:.1f} meq/100g")
print(f"  Difference: {top_cec - bottom_cec:.1f} meq/100g")

print(f"\n--- Carbon Storage by Drainage ---")
for dc in drainage_order:
    subset = df[df["drainage_class"] == dc]
    print(f"  {dc}: {subset['carbon_storage_mg_ha'].mean():.1f} Mg/ha")

print(f"\n--- Soil Health by Drainage ---")
for dc in drainage_order:
    subset = df[df["drainage_class"] == dc]
    print(f"  {dc}: {subset['soil_health_score'].mean():.1f}")

print("\n✓ All additional visualizations complete!")
