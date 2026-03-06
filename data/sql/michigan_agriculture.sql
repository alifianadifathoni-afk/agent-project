-- Michigan Agricultural Fields Database Schema
-- 
-- This schema stores agricultural data for analysis including:
-- - Field boundaries (USDA NASS Crop Sequence Boundaries)
-- - Weather data (NASA POWER)
-- - Soil properties (USDA SSURGO)
-- - Cropland Data Layer (CDL) crop classifications
--
-- Version: 1.0
-- Created: 2026-03-06

-- ============================================================
-- FIELD BOUNDARIES
-- ============================================================

CREATE TABLE IF NOT EXISTS fields (
    field_id VARCHAR(50) PRIMARY KEY,
    county VARCHAR(100),
    state VARCHAR(2),
    area_acres DECIMAL(10, 2),
    geometry GEOMETRY(MULTIPOLYGON, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fields_county ON fields(county);
CREATE INDEX idx_fields_state ON fields(state);
CREATE INDEX idx_fields_area ON fields(area_acres);

-- ============================================================
-- WEATHER DATA (NASA POWER)
-- ============================================================

CREATE TABLE IF NOT EXISTS weather_daily (
    id SERIAL PRIMARY KEY,
    field_id VARCHAR(50) REFERENCES fields(field_id),
    date DATE NOT NULL,
    
    -- Temperature (Celsius)
    t2m_max DECIMAL(5, 2),    -- Temperature at 2m max
    t2m_min DECIMAL(5, 2),    -- Temperature at 2m min
    t2m_avg DECIMAL(5, 2),    -- Temperature at 2m average
    
    -- Precipitation
    prectotcorr DECIMAL(8, 4), -- Precipitation corrected (mm/day)
    
    -- Other weather metrics
    rh2m DECIMAL(5, 2),       -- Relative humidity at 2m (%)
    ws2m DECIMAL(6, 2),       -- Wind speed at 2m (m/s)
    srad DECIMAL(6, 2),       -- Solar radiation (W/m²)
    
    -- Derived metrics
    gdd DECIMAL(6, 2),         -- Growing Degree Days
    hdd DECIMAL(6, 2),        -- Heating Degree Days
    cdd DECIMAL(6, 2),        -- Cooling Degree Days
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_weather_field_date UNIQUE (field_id, date)
);

CREATE INDEX idx_weather_field ON weather_daily(field_id);
CREATE INDEX idx_weather_date ON weather_daily(date);
CREATE INDEX idx_weather_year ON weather_daily(EXTRACT(YEAR FROM date));
CREATE INDEX idx_weather_gdd ON weather_daily(gdd);

-- ============================================================
-- SOIL PROPERTIES (USDA SSURGO)
-- ============================================================

CREATE TABLE IF NOT EXISTS soil_horizons (
    id SERIAL PRIMARY KEY,
    field_id VARCHAR(50) REFERENCES fields(field_id),
    horizon_name VARCHAR(20),
    horizon_depth_top_cm DECIMAL(6, 2),
    horizon_depth_bottom_cm DECIMAL(6, 2),
    
    -- Basic properties
    sand_pct DECIMAL(5, 2),
    silt_pct DECIMAL(5, 2),
    clay_pct DECIMAL(5, 2),
    texture_class VARCHAR(30),
    
    -- Chemical properties
    ph DECIMAL(4, 2),
    om_pct DECIMAL(5, 2),     -- Organic matter percentage
    cec DECIMAL(6, 2),        -- Cation Exchange Capacity (meq/100g)
    
    -- Water properties
    awc DECIMAL(5, 3),        -- Available Water Capacity (cm/cm)
    ksat DECIMAL(8, 4),       -- Saturated hydraulic conductivity
    
    -- Classification
    drainage_class VARCHAR(30),
    hydrologic_group VARCHAR(2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_soil_field ON soil_horizons(field_id);
CREATE INDEX idx_soil_ph ON soil_horizons(ph);
CREATE INDEX idx_soil_drainage ON soil_horizons(drainage_class);

-- ============================================================
-- CROPLAND DATA LAYER (CDL)
-- ============================================================

CREATE TABLE IF NOT EXISTS cdl_observations (
    id SERIAL PRIMARY KEY,
    field_id VARCHAR(50) REFERENCES fields(field_id),
    year INTEGER NOT NULL,
    
    -- CDL classification
    cdl_code INTEGER,
    cdl_category VARCHAR(100),
    cdl_category_group VARCHAR(50),
    percentage DECIMAL(5, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_cdl_field_year UNIQUE (field_id, year)
);

CREATE INDEX idx_cdl_field ON cdl_observations(field_id);
CREATE INDEX idx_cdl_year ON cdl_observations(year);
CREATE INDEX idx_cdl_code ON cdl_observations(cdl_code);

-- ============================================================
-- VIEW: Field Summary
-- ============================================================

CREATE OR REPLACE VIEW field_summary AS
SELECT 
    f.field_id,
    f.county,
    f.state,
    f.area_acres,
    
    -- Latest soil properties (averaged across horizons)
    ROUND(AVG(sh.ph), 2) as avg_ph,
    ROUND(AVG(sh.om_pct), 2) as avg_organic_matter_pct,
    ROUND(AVG(sh.clay_pct), 2) as avg_clay_pct,
    ROUND(AVG(sh.cec), 2) as avg_cec,
    
    -- Weather averages
    ROUND(AVG(w.t2m_avg), 2) as avg_temp_c,
    ROUND(SUM(w.prectotcorr), 2) as total_precip_mm,
    ROUND(SUM(w.gdd), 2) as total_gdd,
    
    -- Latest CDL
    c.cdl_category as current_crop
    
FROM fields f
LEFT JOIN soil_horizons sh ON f.field_id = sh.field_id
LEFT JOIN weather_daily w ON f.field_id = w.field_id
LEFT JOIN cdl_observations c ON f.field_id = c.field_id 
    AND c.year = (SELECT MAX(year) FROM cdl_observations WHERE field_id = f.field_id)

GROUP BY f.field_id, f.county, f.state, f.area_acres, c.cdl_category;

-- ============================================================
-- VIEW: Seasonal Weather Summary
-- ============================================================

CREATE OR REPLACE VIEW seasonal_weather AS
SELECT 
    field_id,
    EXTRACT(YEAR FROM date) as year,
    CASE 
        WHEN EXTRACT(MONTH FROM date) IN (12, 1, 2) THEN 'Winter'
        WHEN EXTRACT(MONTH FROM date) IN (3, 4, 5) THEN 'Spring'
        WHEN EXTRACT(MONTH FROM date) IN (6, 7, 8) THEN 'Summer'
        ELSE 'Fall'
    END as season,
    
    ROUND(AVG(t2m_avg), 2) as avg_temp_c,
    ROUND(SUM(prectotcorr), 2) as total_precip_mm,
    ROUND(SUM(gdd), 2) as total_gdd
    
FROM weather_daily
GROUP BY field_id, year, season;

-- ============================================================
-- SAMPLE QUERIES
-- ============================================================

-- Get all fields in a county
-- SELECT * FROM fields WHERE county = 'Lenawee';

-- Get weather data for a specific field and year
-- SELECT * FROM weather_daily 
-- WHERE field_id = '260910001561001' 
-- AND date BETWEEN '2024-01-01' AND '2024-12-31';

-- Get soil profile for a field
-- SELECT * FROM soil_horizons 
-- WHERE field_id = '260910001561001'
-- ORDER BY horizon_depth_top_cm;

-- Get CDL crop history for a field
-- SELECT year, cdl_category, percentage 
-- FROM cdl_observations
-- WHERE field_id = '260910001561001'
-- ORDER BY year;

-- Calculate annual GDD for all fields
-- SELECT field_id, EXTRACT(YEAR FROM date) as year, SUM(gdd) as annual_gdd
-- FROM weather_daily
-- GROUP BY field_id, year
-- ORDER BY field_id, year;

-- Find fields with significant temperature trends
-- WITH yearly_avg AS (
--     SELECT field_id, EXTRACT(YEAR FROM date) as year, AVG(t2m_avg) as avg_temp
--     FROM weather_daily
--     GROUP BY field_id, year
-- )
-- SELECT field_id, 
--        REGR_SLOPE(avg_temp, year) * 10 as temp_trend_per_decade,
--        CORR(avg_temp, year) as correlation
-- FROM yearly_avg
-- GROUP BY field_id
-- HAVING COUNT(*) > 2;

-- Soil correlation analysis
-- SELECT 
--     CORR(clay_pct, cec) as clay_cec_correlation,
--     CORR(sand_pct, cec) as sand_cec_correlation,
--     CORR(om_pct, cec) as om_cec_correlation,
--     CORR(ph, cec) as ph_cec_correlation
-- FROM soil_horizons;
