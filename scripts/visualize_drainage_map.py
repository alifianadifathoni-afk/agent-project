#!/usr/bin/env python3
"""Visualize spatial distribution of soil drainage classes across field cluster.

Creates a choropleth map with OpenStreetMap base layer showing drainage class for each field.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import contextily as ctx
from adjustText import adjust_text

# Load data
fields = gpd.read_file("data/fields_clustered_30.geojson")
soil = pd.read_csv("data/soil_erosion_carbon_analysis.csv")

# Merge drainage class onto fields
fields = fields.merge(
    soil[["field_id", "drainage_class", "soil_health_score", "om_avg"]], on="field_id"
)

# Color map for drainage classes
drainage_colors = {
    "Well drained": "#27ae60",  # Green
    "Moderately well drained": "#f39c12",  # Orange
    "Somewhat poorly drained": "#1abc9c",  # Teal
    "Poorly drained": "#3498db",  # Blue
}

# Create figure
fig, ax = plt.subplots(figsize=(14, 11))

# Assign colors based on drainage class
fields["color"] = fields["drainage_class"].map(drainage_colors)

# Plot fields with colors
for drainage_class, color in drainage_colors.items():
    subset = fields[fields["drainage_class"] == drainage_class]
    subset.plot(ax=ax, color=color, edgecolor="black", linewidth=1, alpha=0.7, label=drainage_class)

# Add field ID labels
texts = []
for idx, row in fields.iterrows():
    centroid = row.geometry.centroid
    texts.append(
        ax.annotate(
            row["field_id"], xy=(centroid.x, centroid.y), fontsize=8, fontweight="bold", ha="center"
        )
    )

# Adjust text to avoid overlap
try:
    adjust_text(texts, arrowprops=dict(arrowstyle="-", color="gray", lw=0.5))
except:
    pass  # If adjustText fails, labels stay in place

# Add OpenStreetMap base layer
try:
    ctx.add_basemap(ax, crs=fields.crs.to_string(), zoom=12)
except:
    # Fallback: simpler basemap
    ctx.add_basemap(ax, crs="EPSG:4326", source=ctx.providers.CartoDB.Positron)

# Set extent to bounding box with padding
bounds = fields.total_bounds  # [minx, miny, maxx, maxy]
padding = 0.02
ax.set_xlim(bounds[0] - padding, bounds[2] + padding)
ax.set_ylim(bounds[1] - padding, bounds[3] + padding)

# Create legend
legend_patches = [
    mpatches.Patch(color=color, label=class_name, alpha=0.7)
    for class_name, color in drainage_colors.items()
]
ax.legend(
    handles=legend_patches, loc="upper left", title="Drainage Class", fontsize=10, title_fontsize=12
)

# Title and labels
ax.set_title(
    "Soil Drainage Classes - Iowa Corn Belt Field Cluster\n(30 Fields)",
    fontsize=16,
    fontweight="bold",
    pad=15,
)
ax.set_xlabel("Longitude", fontsize=12)
ax.set_ylabel("Latitude", fontsize=12)

# Add summary stats
drainage_counts = fields["drainage_class"].value_counts()
stats_text = "\n".join([f"{cls}: {count}" for cls, count in drainage_counts.items()])
ax.text(
    0.02,
    0.02,
    stats_text,
    transform=ax.transAxes,
    fontsize=9,
    verticalalignment="bottom",
    horizontalalignment="left",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.9),
)

plt.tight_layout()
plt.savefig("data/drainage_class_map.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close()

print("✓ Created: data/drainage_class_map.png")
print(f"  Drainage distribution:")
for cls, count in drainage_counts.items():
    print(f"    {cls}: {count} fields")
