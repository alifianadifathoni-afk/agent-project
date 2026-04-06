#!/usr/bin/env python3
"""Visualize Organic Matter comparison between top 10 and bottom 10 fields.

Creates a box plot showing organic matter % distribution for high vs low productivity fields.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load data
df = pd.read_csv("data/soil_erosion_carbon_analysis.csv")

# Get top 10 and bottom 10 by soil health score
top_10 = df.nsmallest(10, "rank").copy()  # rank 1-10 are top (highest health)
bottom_10 = df.nlargest(10, "rank").copy()  # rank 21-30 are bottom (lowest health)

# Add group label
top_10["group"] = "Top 10\n(High Productivity)"
bottom_10["group"] = "Bottom 10\n(Low Productivity)"
combined = pd.concat([top_10, bottom_10])

# Calculate statistics
top_om_mean = top_10["om_avg"].mean()
bottom_om_mean = bottom_10["om_avg"].mean()
top_om_median = top_10["om_avg"].median()
bottom_om_median = bottom_10["om_avg"].median()

# Create figure
fig, ax = plt.subplots(figsize=(10, 7))

# Box plot with custom colors
palette = {"Top 10\n(High Productivity)": "#2ecc71", "Bottom 10\n(Low Productivity)": "#e74c3c"}
box = sns.boxplot(data=combined, x="group", y="om_avg", palette=palette, width=0.5, ax=ax)

# Add individual data points
sns.stripplot(data=combined, x="group", y="om_avg", color="black", alpha=0.7, size=8, ax=ax)

# Add field ID labels to points
for i, (idx, row) in enumerate(combined.iterrows()):
    group_idx = 0 if row["group"].startswith("Top") else 1
    ax.annotate(
        row["field_id"],
        xy=(group_idx, row["om_avg"]),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=8,
        alpha=0.8,
    )

# Styling
ax.set_title("Organic Matter %: Top 10 vs Bottom 10 Fields", fontsize=16, fontweight="bold", pad=15)
ax.set_ylabel("Organic Matter (%)", fontsize=12)
ax.set_xlabel("")
ax.set_ylim(0, 8)

# Add statistics annotation
stats_text = f"Top 10: μ={top_om_mean:.2f}%, median={top_om_median:.2f}%\nBottom 10: μ={bottom_om_mean:.2f}%, median={bottom_om_median:.2f}%"
ax.text(
    0.98,
    0.98,
    stats_text,
    transform=ax.transAxes,
    fontsize=10,
    verticalalignment="top",
    horizontalalignment="right",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
)

# Grid
ax.yaxis.grid(True, linestyle="--", alpha=0.3)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(
    "data/om_comparison_top10_vs_bottom10.png", dpi=300, bbox_inches="tight", facecolor="white"
)
plt.close()

print("✓ Created: data/om_comparison_top10_vs_bottom10.png")
print(f"  Top 10 OM: mean={top_om_mean:.2f}%, median={top_om_median:.2f}%")
print(f"  Bottom 10 OM: mean={bottom_om_mean:.2f}%, median={bottom_om_median:.2f}%")
print(f"  Difference: {top_om_mean - bottom_om_mean:.2f} percentage points")
