---
name: field-boundaries
description: Download USDA NASS Crop Sequence Boundaries for agricultural fields. Includes functions for downloading, visualizing, and exporting field boundary data.
version: 1.0.0
author: Boreal Bytes
tags: [usda, nass, boundaries, geospatial, download]
---

# Skill: field-boundaries

## Description

Download and work with USDA NASS Crop Sequence Boundaries for agricultural analysis. This skill provides functions to download field boundary data for specific regions and crops, with built-in visualization and export capabilities.

## When to Use This Skill

- **Getting field boundaries**: Download polygon data for agricultural fields
- **Regional analysis**: Filter by corn belt, great plains, or southeast
- **Crop-specific data**: Filter by corn, soybeans, wheat, or cotton
- **Visualization**: Create maps of downloaded fields
- **Data export**: Convert to GeoJSON or GeoParquet formats

## Prerequisites

```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Example Data

Sample data is included in the `examples/` directory:

- `examples/sample_2_fields.geojson` - 2 real field boundaries from Minnesota

Use these for testing and development:

```python
import geopandas as gpd

# Load example data
fields = gpd.read_file('examples/sample_2_fields.geojson')
print(fields[['field_id', 'area_acres', 'crop_name']])

# Output:
#           field_id  area_acres crop_name
# 0  271623002471299    3.704844      Corn
# 1  271623001561551    6.408551      Corn
```

The example data was downloaded from USDA NASS Crop Sequence Boundaries.

## Quick Start

```bash
# Run in isolated environment
uv run --with geopandas --with matplotlib --with shapely python << 'EOF'
from field_boundaries import download_fields, plot_fields, get_summary

# Download 20 fields from corn belt
fields = download_fields(
    count=20,
    regions=['corn_belt'],
    crops=['corn', 'soybeans'],
    output_path='data/fields_EPSG4326.geojson'
)

# Get summary
summary = get_summary(fields)
print(f"Downloaded {summary['total_fields']} fields")
EOF
```

## Installation (Isolated Environment)

This skill runs in an isolated environment to avoid dependency conflicts:

```bash
# Create dedicated environment for this skill
cd .skills/field-boundaries
uv venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .
```

## Usage Examples

### Example 1: Download and Visualize

```python
from field_boundaries import download_fields, plot_fields, get_summary

# Download fields
fields = download_fields(
    count=20,
    regions=['corn_belt'],
    crops=['corn', 'soybeans'],
    output_path='data/my_fields.geojson'
)

# Get summary
summary = get_summary(fields)
print(f"Fields: {summary['total_fields']}")
print(f"Area: {summary['total_area_acres']:.1f} acres")

# Visualize
plot_fields(
    fields,
    title="Iowa Corn and Soybean Fields",
    color_by='crop_name',
    save_path='data/fields_map.png'
)
```

### Example 2: Filter and Export

```python
from field_boundaries import download_fields, filter_by_size, export_fields

# Download fields
fields = download_fields(count=50)

# Filter large fields (>100 acres)
large_fields = filter_by_size(fields, min_acres=100)
print(f"Large fields: {len(large_fields)}")

# Export in multiple formats
export_fields(large_fields, 'data/large_fields.geojson', 'geojson')
export_fields(large_fields, 'data/large_fields.parquet', 'geoparquet')
```

## Python API Reference

### `download_fields(count, regions, crops, output_path)`

Download field boundaries from USDA NASS.

**Parameters:**

- `count` (int): Number of fields to download (20-50 recommended)
- `regions` (list): Regions to sample from ('corn_belt', 'great_plains', 'southeast')
- `crops` (list): Crop types to include ('corn', 'soybeans', 'wheat', 'cotton')
- `output_path` (str): Output file path (should include EPSG4326)

**Returns:** GeoDataFrame with field boundaries

### `plot_fields(fields, title, color_by, save_path)`

Create a visualization of field boundaries.

**Parameters:**

- `fields` (GeoDataFrame): Field boundaries to visualize
- `title` (str): Plot title
- `color_by` (str): Column to color by ('crop_name', 'region')
- `save_path` (str): Path to save the figure

### `get_summary(fields)`

Get summary statistics for field boundaries.

**Parameters:**

- `fields` (GeoDataFrame): Field boundaries

**Returns:** Dictionary with statistics (total_fields, total_area_acres, avg_field_size, etc.)

### `filter_by_size(fields, min_acres)`

Filter fields by minimum size.

**Parameters:**

- `fields` (GeoDataFrame): Field boundaries
- `min_acres` (float): Minimum field size in acres

**Returns:** Filtered GeoDataFrame

### `export_fields(fields, output_path, format)`

Export fields to file.

**Parameters:**

- `fields` (GeoDataFrame): Field boundaries
- `output_path` (str): Output file path
- `format` (str): 'geojson' or 'geoparquet'

## Data Source

- **Source**: USDA NASS Crop Sequence Boundaries
- **Coverage**: Contiguous United States
- **Update Frequency**: Annual
- **Format**: GeoJSON (vector)
- **CRS**: EPSG:4326 (WGS84)

## Output Files

- `*_EPSG4326.geojson` - Field boundaries in GeoJSON format
- `*_EPSG4326.parquet` - Field boundaries in GeoParquet format (cloud-optimized)

## Environment Variables

No special environment variables required. The skill uses public USDA data.

## Resources

- [USDA NASS Crop Sequence Boundaries](https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/)
- [GeoPandas Documentation](https://geopandas.org/)
- [EPSG:4326 - WGS 84](https://epsg.io/4326)
