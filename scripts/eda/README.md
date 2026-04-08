# Agricultural EDA Scripts

Modular scripts for agricultural exploratory data analysis, designed for dashboard integration.

## Quick Start

```bash
# Run full pipeline
python scripts/eda/run_all.py

# Or run individual scripts
python scripts/eda/01_download_data.py
python scripts/eda/02_merge_data.py
python scripts/eda/03_correlation.py
python scripts/eda/04_crop_compare.py
python scripts/eda/05_dashboard_export.py
```

## Scripts

| Script                   | Description                                                          |
| ------------------------ | -------------------------------------------------------------------- |
| `01_download_data.py`    | Generate/download all data layers (fields, soil, weather, CDL, NDVI) |
| `02_merge_data.py`       | Merge all layers into single `merged_eda_data.csv`                   |
| `03_correlation.py`      | Correlation matrix, heatmap, significance tests                      |
| `04_crop_compare.py`     | Corn vs soybeans comparison (t-tests, box plots)                     |
| `05_dashboard_export.py` | Export dashboard-ready JSON files                                    |
| `run_all.py`             | Run all scripts in sequence                                          |
| `utils.py`               | Shared helper functions                                              |

## Data Layers

| Layer            | Source                 | Records                         |
| ---------------- | ---------------------- | ------------------------------- |
| Field boundaries | USDA NASS (synthetic)  | 50 fields                       |
| Soil             | SSURGO (synthetic)     | 150 (3 horizons × 50 fields)    |
| Weather          | NASA POWER             | 54,800 (1,096 days × 50 fields) |
| CDL Crop Type    | USDA NASS (synthetic)  | 150 (3 years × 50 fields)       |
| NDVI             | Sentinel-2 (synthetic) | 50                              |

## Output Structure

```
output/
├── fields_50_cornbelt.geojson       # Field boundaries
├── soil_data_50_fields.csv          # Raw soil data
├── weather_50_fields_2022_2024.csv   # Raw weather data
├── cdl_50_fields.csv                # Crop type data
├── ndvi_50_fields.csv               # NDVI data
│
└── eda/
    ├── merged_eda_data.csv           # Merged dataset
    ├── correlations/
    │   ├── correlation_matrix.csv
    │   ├── strongest_correlations.csv
    │   ├── significance_tests.json
    │   ├── correlation_heatmap.png
    │   └── scatter_*.png
    ├── comparisons/
    │   ├── crop_statistics.csv
    │   ├── ttest_results.json
    │   ├── summary.json
    │   ├── boxplots/*.png
    │   └── violin/*.png
    └── dashboard/
        ├── fields.json
        ├── crop_distribution.json
        ├── soil_summary.json
        ├── weather_summary.json
        ├── ndvi_summary.json
        ├── kpis.json
        └── monthly_weather.json
```

## Variables

### Field Attributes

- `field_id` - Unique identifier
- `state` - US state (IA, IL, IN, MO, OH)
- `region` - corn_belt
- `assigned_crop` - corn or soybeans
- `area_acres` - Field size
- `centroid_lat/lon` - Field center

### Soil Properties

- `soil_om_pct` - Organic matter (%)
- `soil_ph` - pH in water
- `soil_drainage` - Drainage class
- `soil_clay_pct`, `soil_sand_pct`, `soil_silt_pct` - Texture (%)
- `soil_awc` - Available water capacity
- `soil_bulk_density` - Bulk density (g/cm³)
- `soil_cec` - Cation exchange capacity

### Weather (Growing Season Aggregates)

- `gdd_temp_mean` - Mean temperature (°C)
- `gdd_temp_max/min` - Temperature range
- `gdd_precip_total` - Total precipitation (mm)
- `gdd_solar_total` - Total solar radiation
- `gdd_humidity_mean` - Mean humidity (%)

### NDVI

- `ndvi_peak` - Peak NDVI
- `ndvi_mean` - Mean NDVI
- `ndvi_std` - NDVI standard deviation

## Dashboard Integration

The `05_dashboard_export.py` script exports JSON files ready for web dashboards:

- `kpis.json` - KPI cards (total fields, acres, crop counts, averages)
- `fields.json` - Full field data with nested soil/weather/NDVI
- `crop_distribution.json` - Crop counts by state
- `monthly_weather.json` - Time series for charts

## Requirements

```bash
pip install pandas numpy matplotlib seaborn scipy geopandas shapely requests
```

Or use UV:

```bash
uv run --with pandas --with numpy --with matplotlib --with seaborn --with scipy --with geopandas python scripts/eda/run_all.py
```

## Customization

### Change Field Count

Edit `01_download_data.py`:

```python
generate_fields(count=100)  # Change 50 to 100
```

### Change Weather Years

Edit `01_download_data.py`:

```python
start = "20200101"  # Change start year
end = "20241231"    # Change end year
```

### Add Real Data

Replace synthetic data generation functions with real API calls:

- `download_weather()` - Already uses real NASA POWER API
- `download_soil()` - Add real NRCS SDA queries
- `generate_cdl()` - Add real CDL raster clipping

## License

Apache 2.0 - See LICENSE file
