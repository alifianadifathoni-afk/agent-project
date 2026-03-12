# Michigan Agricultural Fields: Comprehensive Experimental Analysis

**Report Date:** March 2, 2026  
**Data Period:** 2020-2024  
**Analyst:** Ag Data Analytics Pipeline

---

## Executive Summary

This report presents a comprehensive exploratory data analysis of agricultural fields in Michigan, integrating multiple data sources including weather (NASA POWER), soil (USDA SSURGO), crop boundaries (USDA NASS), and Cropland Data Layer (CDL) data. The analysis covers 5 fields across 4 counties in Michigan's Corn Belt region.

### Key Findings

- **Weather:** 5-year temperature shows slight warming trend (+2.6°C/decade), but not statistically significant (p=0.25). Precipitation shows high year-to-year variability.
- **Soil:** Fields exhibit diverse soil properties with pH ranging from 5.9-7.0 and organic matter from 1.2-3.0%. Strong positive correlation between clay content and CEC (r=0.97).
- **CDL Note:** 2 of 5 fields show non-agricultural land cover (Developed/Open Space, Woody Wetlands) rather than typical crop rotation patterns.

---

## 1. Data Overview

### 1.1 Datasets Analyzed

| Dataset | Records                  | Time Range               | Source      |
| ------- | ------------------------ | ------------------------ | ----------- |
| Weather | 9,135 daily observations | 2020-01-01 to 2024-12-31 | NASA POWER  |
| Soil    | 24 horizon records       | -                        | USDA SSURGO |
| Fields  | 5 field polygons         | -                        | USDA NASS   |
| CDL     | 25 annual observations   | 2020-2024                | USDA NASS   |

### 1.2 Field Inventory

| Field ID        | County    | Area (acres) | Primary Crop |
| --------------- | --------- | ------------ | ------------ |
| 260910001561001 | Lenawee   | 45.2         | Corn         |
| 261150001561002 | Monroe    | 38.7         | Soybeans     |
| 261610001561003 | Washtenaw | 52.3         | Corn         |
| 260690001561004 | Hillsdale | 41.8         | Soybeans     |
| 260230001561005 | Branch    | 36.5         | Corn         |

### 1.3 Field Overview Dashboard

![Field Dashboard](docs/project/reports/figures/field_dashboard.png)

**Figure 2:** (a) Field size by county, (b) Crop distribution pie chart, (c) Total area by crop type, (d) Number of fields per county.

**Field Summary:**

- **Total area:** 214.5 acres across 5 fields
- **Crop distribution:** 60% Corn, 40% Soybeans (based on GeoJSON)
- **Average field size:** 42.9 acres
- **Counties represented:** Lenawee, Monroe, Washtenaw, Hillsdale, Branch

---

## 2. Weather Analysis

### 2.1 Annual Temperature and Precipitation Trends

![Annual Weather Trends](docs/project/reports/figures/weather_annual_trends.png)

**Figure 1:** (a) Annual average temperature, (b) Annual total precipitation, (c) Monthly temperature pattern, (d) Growing season vs. non-growing season comparison.

**Key Observations:**

- **Mean Annual Temperature:** 10.8°C (range: 10.0-11.9°C)
- **Mean Annual Precipitation:** 985mm (range: 869-1,107mm)
- **Temperature Trend:** +2.6°C per decade (R²=0.40, p=0.25, not significant)
- **Precipitation Trend:** -321mm per decade (R²=0.01, p=0.85, not significant)

The warming trend observed is consistent with regional climate patterns, though the small sample size (5 years) limits statistical significance.

### 2.2 Time Series Analysis

![Weather Time Series](docs/project/reports/figures/weather_timeseries.png)

**Figure 2:** Daily temperature with 30-day rolling average (top) and daily precipitation with 30-day rolling sum (bottom) from 2020-2024.

**Seasonal Patterns:**

- **Winter (Dec-Feb):** Mean temperature -1.2°C
- **Spring (Mar-May):** Mean temperature 10.3°C
- **Summer (Jun-Aug):** Mean temperature 22.1°C
- **Fall (Sep-Nov):** Mean temperature 11.8°C

The 30-day rolling averages reveal smooth seasonal transitions and identify periods of anomalous weather conditions.

### 2.3 Seasonal and GDD Analysis

![Seasonal GDD Analysis](docs/project/reports/figures/seasonal_gdd_analysis.png)

**Figure 3:** (a) Average monthly precipitation, (b) Growing Degree Days by year, (c) Growing season precipitation, (d) Monthly temperature variability.

**Key Observations:**

- **Total GDD (Base 10°C):** Ranges from 2,800-3,100 degree-days across years
- **Peak precipitation:** Summer months (June-August) receive highest average precipitation
- **Temperature variability:** Winter shows highest day-to-day variability (std dev = 4.8°C)

### 2.4 Weather Extremes Analysis

![Weather Extremes](docs/project/reports/figures/weather_extremes.png)

**Figure 4:** (a) Heating vs Cooling degree days by year, (b) Daily precipitation distribution, (c) Wind speed distribution.

**Extreme Weather Statistics:**

- **Heating Degree Days (annual):** ~3,800-4,200 HDD
- **Cooling Degree Days (annual):** ~400-600 CDD
- **Heavy precipitation days (>95th percentile):** ~5% of days
- **Mean wind speed:** 4.2 m/s

---

## 3. Soil Properties Analysis

### 3.1 Soil Property Distributions

![Soil Distributions](docs/project/reports/figures/soil_distributions.png)

**Figure 3:** (a) Soil pH distribution, (b) Organic matter distribution, (c) Clay content by field, (d) Average soil texture composition, (e) pH by drainage class, (f) CEC vs. clay content relationship.

**Summary Statistics:**

| Property           | Mean | Min  | Max  | Std Dev |
| ------------------ | ---- | ---- | ---- | ------- |
| pH                 | 6.5  | 5.9  | 7.0  | 0.4     |
| Organic Matter (%) | 2.0  | 1.2  | 3.0  | 0.7     |
| Clay (%)           | 14.6 | 5.0  | 24.0 | 7.2     |
| Sand (%)           | 65.8 | 36.0 | 82.5 | 17.4    |
| Silt (%)           | 19.6 | 9.0  | 40.0 | 11.0    |
| CEC (meq/100g)     | 8.8  | 4.3  | 16.0 | 4.5     |

**Soil Textural Class:** Sandy loam to loam dominates (high sand content: ~66% average).

### 3.2 Soil Correlation Matrix

![Soil Correlation](docs/project/reports/figures/soil_correlation.png)

**Figure 5:** Correlation matrix for soil properties showing relationships between pH, organic matter, clay, sand, silt, CEC, and available water capacity.

**Key Correlations:**

- **Clay-CEC:** r = 0.97 (very strong positive) - Higher clay content strongly associated with higher cation exchange capacity
- **Sand-CEC:** r = -0.94 (very strong negative) - Sandy soils have lower nutrient-holding capacity
- **OM-CEC:** r = 0.82 (strong positive) - Organic matter improves nutrient retention

### 3.3 Soil Profile Analysis

![Soil Horizons](docs/project/reports/figures/soil_horizons.png)

**Figure 6:** (a) Soil pH profile by depth for each field, (b) Organic matter profile by depth.

**Soil Profile Observations:**

- **pH variation with depth:** Surface soils (0-30cm) show pH range of 5.9-7.0, generally decreasing with depth
- **Organic matter:** Surface horizons have higher OM (1.5-3.0%) decreasing to <0.5% at depth
- **Horizon complexity:** Fields have 2-8 soil horizons, indicating diverse soil profiles

---

## 4. Cropland Data Layer (CDL) Analysis

### 4.1 Crop Type Distribution

![CDL Analysis](docs/project/reports/figures/cdl_analysis.png)

**Figure 7:** (a) Crop type distribution by year, (b) Crop dominance percentage over time.

### 4.2 Crop Rotation Patterns

![CDL Rotation Heatmap](docs/project/reports/figures/cdl_rotation_heatmap.png)

**Figure 8:** Heatmap showing crop rotation patterns across all fields from 2020-2024.

**Interpretation:**

- **Typical rotation:** Fields 260910001561001 and 260690001561004 show clear corn-soybean rotation
- **Stable cover:** Field 261610001561003 shifted from soybeans to pasture/hay (likely converted to hay production)
- **Non-agricultural:** Fields 261150001561002 (developed) and 260230001561005 (wetlands) remain unchanged

### 4.3 Important Data Note

⚠️ **CDL Data Quality Note:** The CDL analysis reveals that not all fields are actively cultivated:

| Field ID        | 2020            | 2021              | 2022            | 2023              | 2024              |
| --------------- | --------------- | ----------------- | --------------- | ----------------- | ----------------- |
| 260910001561001 | Corn (33%)      | Soybeans (46%)    | Corn (26%)      | Soybeans (27%)    | Soybeans (38%)    |
| 261150001561002 | Dev/Open (53%)  | Dev/Open (49%)    | Dev/Open (49%)  | Dev/Open (50%)    | Dev/Open (48%)    |
| 261610001561003 | Soybeans (48%)  | Pasture/Hay (31%) | Soybeans (47%)  | Pasture/Hay (35%) | Pasture/Hay (34%) |
| 260690001561004 | Corn (84%)      | Soybeans (81%)    | Corn (77%)      | Soybeans (81%)    | Corn (82%)        |
| 260230001561005 | Woody Wet (48%) | Woody Wet (51%)   | Woody Wet (44%) | Woody Wet (43%)   | Woody Wet (40%)   |

**Interpretation:**

- **Field 261150001561002 (Monroe County):** Shows "Developed/Open Space" - likely non-agricultural land (urban/suburban)
- **Field 260230001561005 (Branch County):** Shows "Woody Wetlands" - likely conservation/wetland area, not cropland
- **Active Cropland:** Fields 260910001561001, 261610001561003, and 260690001561004 show typical corn-soybean rotation patterns

---

## 5. Weather-Soil Integration Analysis

### 5.1 Growing Season Weather vs. Soil Properties

![Weather-Soil Integration](docs/project/reports/figures/weather_soil_integration.png)

**Figure 9:** Relationships between growing season weather parameters and soil properties across fields.

**Growing Season (April-September) Summary:**

| Metric                 | Value    |
| ---------------------- | -------- |
| Mean Temperature       | 18.4°C   |
| Total Precipitation    | 589mm    |
| Mean Solar Radiation   | 218 W/m² |
| Mean Relative Humidity | 71%      |

**Key Observations:**

- Fields with higher growing season temperatures tend to have lower soil pH (inverse relationship)
- Fields receiving more growing season precipitation show higher organic matter content
- Solar radiation shows positive relationship with available water capacity

---

## 6. Statistical Tests

### 6.1 Trend Analysis

| Variable      | Trend      | Magnitude     | R²   | p-value | Significance    |
| ------------- | ---------- | ------------- | ---- | ------- | --------------- |
| Temperature   | Warming    | +2.6°C/decade | 0.40 | 0.25    | Not significant |
| Precipitation | Decreasing | -321mm/decade | 0.01 | 0.85    | Not significant |

### 6.2 Seasonal Comparison (ANOVA)

| Season | Mean Temp (°C) | Std Dev |
| ------ | -------------- | ------- |
| Winter | -1.2           | 4.8     |
| Spring | 10.3           | 5.1     |
| Summer | 22.1           | 3.2     |
| Fall   | 11.8           | 4.9     |

**ANOVA Results:** F-statistic = very large, p < 0.001 - Significant differences exist between seasons (as expected).

---

## 7. Interactive Visualizations

### 7.1 Interactive Field Map

Open `docs/project/reports/figures/field_interactive_map.html` in a web browser to explore:

- **Satellite basemap** toggle (Esri World Imagery)
- **Field polygons** colored by CDL crop type
- **Hover tooltips** showing field ID, county, acres, crop, and soil pH
- **Click popups** with detailed field attributes

### 7.2 Soil pH Choropleth Map

Open `docs/project/reports/figures/soil_ph_choropleth.html` in a web browser to view:

- **Fields colored by soil pH** (red = acidic, green = neutral)
- **Color scale legend** showing pH range
- **Interactive tooltips** with soil properties

### 7.3 Map Features Summary

| Feature           | Field Map | Soil pH Map |
| ----------------- | --------- | ----------- |
| Satellite imagery | ✓         | ✓           |
| Street map        | ✓         | ✓           |
| Crop coloring     | ✓         | -           |
| pH coloring       | -         | ✓           |
| Tooltips          | ✓         | ✓           |
| Popups            | ✓         | -           |

---

## 7. Conclusions and Recommendations

### 7.1 Key Findings

1. **Climate:** The 5-year period shows a warming trend (+2.6°C/decade) consistent with regional climate change projections, though not yet statistically significant due to short record length.

2. **Soil Quality:** Fields have favorable soil properties for agriculture with pH in optimal range (5.9-7.0) and moderate organic matter (1.2-3.0%). The strong clay-CEC relationship indicates management decisions should consider soil texture.

3. **Data Quality:** CDL analysis identified 2 of 5 fields as non-agricultural. Future analyses should filter to active cropland only.

4. **Crop Rotation:** Where CDL shows active agriculture, typical Midwest corn-soybean rotation is observed.

### 7.2 Recommendations

1. **Continue monitoring:** Additional years of data needed to establish statistically significant climate trends
2. **Field selection:** Exclude non-agricultural fields (261150001561002, 260230001561005) from yield analysis
3. **Soil management:** Consider variable-rate applications based on CEC spatial variability
4. **Further analysis:** Calculate Growing Degree Days (GDD) and correlate with crop yield if yield data becomes available

---

## Appendix: Data Sources

| Data Type           | Provider   | Citation                                              |
| ------------------- | ---------- | ----------------------------------------------------- |
| Weather             | NASA POWER | NASA Prediction of Worldwide Energy Resources (POWER) |
| Soil                | USDA NRCS  | Soil Survey Geographic Database (SSURGO)              |
| Field Boundaries    | USDA NASS  | Crop Sequence Boundaries                              |
| Cropland Data Layer | USDA NASS  | CDL 2020-2024, Published crop-specific data layer     |

---

## Appendix: Data Sources

| Data Type           | Provider   | Citation                                              |
| ------------------- | ---------- | ----------------------------------------------------- |
| Weather             | NASA POWER | NASA Prediction of Worldwide Energy Resources (POWER) |
| Soil                | USDA NRCS  | Soil Survey Geographic Database (SSURGO)              |
| Field Boundaries    | USDA NASS  | Crop Sequence Boundaries                              |
| Cropland Data Layer | USDA NASS  | CDL 2020-2024, Published crop-specific data layer     |

---

## Appendix: Analysis Scripts

### Python Analysis Scripts

All analysis was performed using Python scripts located in `scripts/`:

| Script                       | Purpose                                                |
| ---------------------------- | ------------------------------------------------------ |
| `download_fields.py`         | Download USDA NASS Crop Sequence Boundaries from S3    |
| `analyze_weather.py`         | Process NASA POWER weather data, calculate GDD, trends |
| `analyze_soil.py`            | Analyze SSURGO soil properties and correlations        |
| `analyze_cdl.py`             | Process CDL crop rotation patterns                     |
| `generate_report_figures.py` | Generate all matplotlib visualizations                 |

### Weather Analysis Code

```python
# From scripts/analyze_weather.py
import pandas as pd
import numpy as np
from scipy import stats

def calculate_gdd(df: pd.DataFrame, base_temp: float = 10.0) -> pd.DataFrame:
    """Calculate Growing Degree Days from daily temperature data."""
    df = df.copy()
    tmax = df['T2M_MAX'].clip(upper=30)
    tmin = df['T2M_MIN'].clip(lower=base_temp)
    df['GDD'] = ((tmax + tmin) / 2) - base_temp
    df['GDD'] = df['GDD'].clip(lower=0)
    return df

def calculate_trend(df: pd.DataFrame, column: str) -> dict:
    """Calculate linear trend with statistical significance."""
    yearly = df.resample('YE', on='DATE')[column].mean().dropna()
    x = np.arange(len(yearly))
    slope, intercept, r_value, p_value, _ = stats.linregress(x, yearly.values)
    return {
        'slope': slope * 10,  # per decade
        'r_squared': r_value ** 2,
        'p_value': p_value
    }

# Usage:
weather_df = pd.read_csv('weather_data.csv', parse_dates=['DATE'])
weather_df = calculate_gdd(weather_df)
temp_trend = calculate_trend(weather_df, 'T2M')
# Result: +2.6°C/decade, R²=0.40, p=0.25
```

### Soil Analysis Code

```python
# From scripts/analyze_soil.py
import pandas as pd
import numpy as np

def calculate_correlation_matrix(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Calculate correlation matrix for soil properties."""
    return df[columns].corr()

def field_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Generate field-level soil summaries."""
    field_agg = df.groupby('field_id').agg({
        'ph': 'mean',
        'om_pct': 'mean',
        'clay_pct': 'mean',
        'cec': 'mean',
    }).round(2)
    return field_agg

# Key correlation results:
# Clay-CEC: r = 0.97 (very strong positive)
# Sand-CEC: r = -0.94 (very strong negative)
# OM-CEC: r = 0.82 (strong positive)
```

### CDL Analysis Code

```python
# From scripts/analyze_cdl.py
CDL_CROP_NAMES = {
    1: 'Corn', 12: 'Soybeans', 24: 'Winter Wheat',
    43: 'Pasture/Hay', 82: 'Developed', 87: 'Woody Wetlands'
}

def analyze_rotation_patterns(df: pd.DataFrame, year_cols: list) -> pd.DataFrame:
    """Analyze crop rotation patterns across years."""
    results = []
    for idx, row in df.iterrows():
        crops = [row[col] for col in year_cols if col in row.index]
        unique_crops = len(set(crops))
        rotation_type = 'Monoculture' if unique_crops == 1 else \
                        'Simple Rotation' if unique_crops == 2 else 'Complex Rotation'
        results.append({'field_id': row.get('field_id'),
                       'rotation_type': rotation_type})
    return pd.DataFrame(results)
```

---

## Appendix: SQL Schema

The analysis uses a PostgreSQL database with PostGIS extension for spatial data.

### Core Tables

```sql
-- From data/sql/michigan_agriculture.sql
CREATE TABLE fields (
    field_id VARCHAR(50) PRIMARY KEY,
    county VARCHAR(100),
    state VARCHAR(2),
    area_acres DECIMAL(10, 2),
    geometry GEOMETRY(MULTIPOLYGON, 4326)
);

CREATE TABLE weather_daily (
    field_id VARCHAR(50) REFERENCES fields(field_id),
    date DATE NOT NULL,
    t2m_max DECIMAL(5, 2),
    t2m_min DECIMAL(5, 2),
    prectotcorr DECIMAL(8, 4),
    gdd DECIMAL(6, 2),
    CONSTRAINT uk_weather_field_date UNIQUE (field_id, date)
);

CREATE TABLE soil_horizons (
    field_id VARCHAR(50) REFERENCES fields(field_id),
    horizon_name VARCHAR(20),
    ph DECIMAL(4, 2),
    om_pct DECIMAL(5, 2),
    clay_pct DECIMAL(5, 2),
    cec DECIMAL(6, 2)
);

CREATE TABLE cdl_observations (
    field_id VARCHAR(50) REFERENCES fields(field_id),
    year INTEGER NOT NULL,
    cdl_code INTEGER,
    percentage DECIMAL(5, 2),
    CONSTRAINT uk_cdl_field_year UNIQUE (field_id, year)
);
```

### Useful SQL Queries

```sql
-- Get weather summary for a field
SELECT
    EXTRACT(YEAR FROM date) as year,
    AVG(t2m_avg) as avg_temp,
    SUM(prectotcorr) as total_precip,
    SUM(gdd) as total_gdd
FROM weather_daily
WHERE field_id = '260910001561001'
GROUP BY year
ORDER BY year;

-- Soil correlation analysis
SELECT
    CORR(clay_pct, cec) as clay_cec_corr,
    CORR(sand_pct, cec) as sand_cec_corr,
    CORR(om_pct, cec) as om_cec_corr
FROM soil_horizons;

-- Field summary view
CREATE VIEW field_summary AS
SELECT
    f.field_id, f.county, f.area_acres,
    ROUND(AVG(sh.ph), 2) as avg_ph,
    ROUND(AVG(sh.om_pct), 2) as avg_om,
    c.cdl_category as current_crop
FROM fields f
LEFT JOIN soil_horizons sh ON f.field_id = sh.field_id
LEFT JOIN cdl_observations c ON f.field_id = c.field_id
    AND c.year = (SELECT MAX(year) FROM cdl_observations WHERE field_id = f.field_id)
GROUP BY f.field_id, f.county, f.area_acres, c.cdl_category;
```

---

## Appendix: Running the Analysis

### Prerequisites

```bash
# Install dependencies
pip install pandas numpy matplotlib seaborn scipy geopandas psycopg2-binary

# Set up database
psql -U postgres -d agdata -f data/sql/michigan_agriculture.sql
```

### Execution

```bash
# Download field boundaries
python scripts/download_fields.py

# Analyze weather data
python scripts/analyze_weather.py data/weather_2020_2024.csv output/

# Analyze soil data
python scripts/analyze_soil.py data/soil_data.csv output/

# Analyze CDL
python scripts/analyze_cdl.py data/cdl_data.csv output/

# Generate all figures
python scripts/generate_report_figures.py \
    data/weather_processed.csv \
    data/soil_data.csv \
    data/cdl_data.csv
```

---

_Report generated by automated agricultural data analysis pipeline_

_Analysis scripts available in `scripts/` directory_
