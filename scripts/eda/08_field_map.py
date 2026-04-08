"""Geospatial map generation for agricultural fields.

Creates interactive Leaflet maps combining field boundaries with
soil properties, NDVI, and crop data. Uses choropleth styling
and layer controls.

Usage:
    python scripts/eda/08_field_map.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path

import geopandas as gpd
import pandas as pd

LEAFLET_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Corn Belt Agricultural Dashboard</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet-control-layers@1.5.1/dist/leaflet.control-layers.css" />
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        #map { height: 100vh; width: 100vw; }
        .sidebar {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 320px;
            max-height: calc(100vh - 20px);
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .sidebar-header {
            background: #2c3e50;
            color: white;
            padding: 15px;
            font-weight: 600;
            font-size: 14px;
        }
        .sidebar-content {
            padding: 15px;
            overflow-y: auto;
            flex: 1;
        }
        .layer-select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            margin-bottom: 15px;
        }
        .field-info {
            margin-bottom: 15px;
        }
        .field-info h3 {
            font-size: 16px;
            color: #2c3e50;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid #eee;
        }
        .field-info .row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            font-size: 13px;
            border-bottom: 1px solid #f5f5f5;
        }
        .field-info .label {
            color: #7f8c8d;
        }
        .field-info .value {
            font-weight: 500;
            color: #2c3e50;
        }
        .legend {
            padding: 10px 0;
        }
        .legend-title {
            font-weight: 600;
            font-size: 13px;
            margin-bottom: 8px;
        }
        .legend-scale {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .legend-scale span {
            font-size: 11px;
        }
        .color-box {
            width: 20px;
            height: 12px;
            border-radius: 2px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 10px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            text-align: center;
        }
        .stat-card .value {
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
        }
        .stat-card .label {
            font-size: 11px;
            color: #7f8c8d;
            margin-top: 4px;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="sidebar">
        <div class="sidebar-header">Agricultural Field Dashboard</div>
        <div class="sidebar-content">
            <select id="layerSelect" class="layer-select">
                <option value="crop">Crop Type</option>
                <option value="ndvi_peak">NDVI (Peak)</option>
                <option value="ndvi_mean">NDVI (Mean)</option>
                <option value="soil_om">Soil Organic Matter</option>
                <option value="soil_ph">Soil pH</option>
            </select>
            <div id="fieldInfo" class="field-info">
                <p style="color: #7f8c8d; font-size: 13px;">Click a field to view details</p>
            </div>
            <div id="legend" class="legend"></div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="value">{{n_fields}}</div>
                    <div class="label">Total Fields</div>
                </div>
                <div class="stat-card">
                    <div class="value">{{n_corn}}</div>
                    <div class="label">Corn Fields</div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const FIELDS = {{fields_json}};
        
        const LAYER_STYLES = {
            crop: {
                colors: {'corn': '#f39c12', 'soybeans': '#27ae60'},
                getColor: d => d ? LAYER_STYLES.crop.colors[d] || '#95a5a6' : '#95a5a6',
                legend: [
                    { color: '#f39c12', label: 'Corn' },
                    { color: '#27ae60', label: 'Soybeans' }
                ]
            },
            ndvi_peak: {
                colors: ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60', '#1a9850'],
                domain: [0.5, 0.95],
                getColor: d => d ? getSequentialColor(d, LAYER_STYLES.ndvi_peak) : '#95a5a6',
                legend: [
                    { color: '#d73027', label: '0.5 (Low)' },
                    { color: '#fc8d59', label: '0.6' },
                    { color: '#fee08b', label: '0.7' },
                    { color: '#d9ef8b', label: '0.8' },
                    { color: '#91cf60', label: '0.9' },
                    { color: '#1a9850', label: '0.95 (High)' }
                ]
            },
            ndvi_mean: {
                colors: ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60', '#1a9850'],
                domain: [0.3, 0.7],
                getColor: d => d ? getSequentialColor(d, LAYER_STYLES.ndvi_mean) : '#95a5a6',
                legend: [
                    { color: '#d73027', label: '0.3 (Low)' },
                    { color: '#1a9850', label: '0.7 (High)' }
                ]
            },
            soil_om: {
                colors: ['#fff7ec', '#fee8c8', '#fdd49e', '#fdbb84', '#fc8d59', '#ef6548', '#d7301f'],
                domain: [1.5, 5.5],
                getColor: d => d ? getSequentialColor(d, LAYER_STYLES.soil_om) : '#95a5a6',
                legend: [
                    { color: '#fff7ec', label: '1.5%' },
                    { color: '#d7301f', label: '5.5%' }
                ]
            },
            soil_ph: {
                colors: ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60', '#1a9850'],
                domain: [5.5, 8.0],
                getColor: d => d ? getSequentialColor(d, LAYER_STYLES.soil_ph) : '#95a5a6',
                legend: [
                    { color: '#d73027', label: '5.5 (Acidic)' },
                    { color: '#1a9850', label: '8.0 (Alkaline)' }
                ]
            }
        };
        
        function getSequentialColor(value, style) {
            const { colors, domain } = style;
            const [min, max] = domain;
            const normalized = Math.max(0, Math.min(1, (value - min) / (max - min)));
            const index = Math.min(colors.length - 1, Math.floor(normalized * colors.length));
            return colors[index];
        }
        
        const map = L.map('map').setView([41.0, -88.0], 6);
        
        const basemaps = {
            streets: L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {
                maxZoom: 19, attribution: '© OpenStreetMap'
            }),
            satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {
                maxZoom: 19, attribution: '© Esri'
            }),
            terrain: L.tileLayer('https://{{s}}.tile.opentopomap.org/{{z}}/{{x}}/{{y}}.png', {
                maxZoom: 17, attribution: '© OpenTopoMap'
            })
        };
        
        basemaps.streets.addTo(map);
        
        L.control.layers(basemaps, {}, { position: 'topleft' }).addTo(map);
        
        let fieldLayer = L.geoJSON(FIELDS, {
            style: feature => {
                const layer = document.getElementById('layerSelect').value;
                const style = LAYER_STYLES[layer];
                return {
                    fillColor: style.getColor(feature.properties[layer === 'soil_om' ? 'soil_om_pct' : layer === 'soil_ph' ? 'soil_ph' : feature.properties.assigned_crop]),
                    fillOpacity: 0.7,
                    weight: 1,
                    color: '#333'
                };
            },
            onEachFeature: (feature, layer) => {
                layer.on('click', () => showFieldInfo(feature.properties));
            }
        }).addTo(map);
        
        map.fitBounds(fieldLayer.getBounds());
        
        function updateLayer() {
            const layer = document.getElementById('layerSelect').value;
            fieldLayer.eachLayer(l => {
                const props = l.feature.properties;
                const style = LAYER_STYLES[layer];
                const value = layer === 'soil_om' ? props.soil_om_pct : 
                             layer === 'soil_ph' ? props.soil_ph :
                             layer === 'crop' ? props.assigned_crop :
                             props[layer];
                l.setStyle({
                    fillColor: style.getColor(value),
                    fillOpacity: 0.7,
                    weight: 1,
                    color: '#333'
                });
            });
            updateLegend(layer);
        }
        
        function updateLegend(layer) {
            const style = LAYER_STYLES[layer];
            const legend = document.getElementById('legend');
            legend.innerHTML = '<div class="legend-title">' + 
                (layer === 'crop' ? 'Crop Type' : 
                 layer === 'ndvi_peak' ? 'NDVI Peak' : 
                 layer === 'ndvi_mean' ? 'NDVI Mean' :
                 layer === 'soil_om' ? 'Soil OM %' : 'Soil pH') + 
                '</div>' +
                style.legend.map(l => 
                    '<div class="legend-scale">' +
                    '<div class="color-box" style="background:' + l.color + '"></div>' +
                    '<span>' + l.label + '</span></div>'
                ).join('');
        }
        
        function showFieldInfo(props) {
            const info = document.getElementById('fieldInfo');
            info.innerHTML = '<h3>' + props.field_id + '</h3>' +
                '<div class="row"><span class="label">State</span><span class="value">' + props.state + '</span></div>' +
                '<div class="row"><span class="label">Crop</span><span class="value">' + props.assigned_crop + '</span></div>' +
                '<div class="row"><span class="label">Area (acres)</span><span class="value">' + props.area_acres.toFixed(1) + '</span></div>' +
                '<div class="row"><span class="label">Soil Type</span><span class="value">' + props.soil_type + '</span></div>' +
                '<div class="row"><span class="label">Drainage</span><span class="value">' + props.soil_drainage + '</span></div>' +
                '<div class="row"><span class="label">OM %</span><span class="value">' + props.soil_om_pct.toFixed(2) + '</span></div>' +
                '<div class="row"><span class="label">pH</span><span class="value">' + props.soil_ph.toFixed(2) + '</span></div>' +
                '<div class="row"><span class="label">NDVI Peak</span><span class="value">' + props.ndvi_peak.toFixed(3) + '</span></div>' +
                '<div class="row"><span class="label">NDVI Mean</span><span class="value">' + props.ndvi_mean.toFixed(3) + '</span></div>';
        }
        
        document.getElementById('layerSelect').addEventListener('change', updateLayer);
        updateLegend('crop');
    </script>
</body>
</html>"""


def load_and_merge_data(
    fields_path: str = "output/fields_50_cornbelt.geojson",
    merged_path: str = "output/eda/merged_eda_data.csv",
) -> gpd.GeoDataFrame:
    """Load field boundaries and merge with data."""
    print("Loading field boundaries...")
    gdf = gpd.read_file(fields_path)
    gdf = gdf.rename(columns={"crop_name": "assigned_crop"})
    print(f"  Loaded {len(gdf)} fields")

    print("Loading merged data...")
    df = pd.read_csv(merged_path)
    print(f"  Loaded {len(df)} records")

    print("Merging data...")
    merge_cols = [
        "field_id",
        "soil_type",
        "soil_drainage",
        "soil_om_pct",
        "soil_ph",
        "soil_awc",
        "soil_clay_pct",
        "soil_bulk_density",
        "soil_cec",
        "gdd_temp_mean",
        "gdd_precip_total",
        "gdd_solar_total",
        "ndvi_peak",
        "ndvi_mean",
        "ndvi_std",
    ]

    merge_df = df[[col for col in merge_cols if col in df.columns]]

    merged = gdf.merge(merge_df, on="field_id", how="left")
    print(f"  Merged {len(merged)} fields with data")

    return merged


def create_interactive_map(
    gdf: gpd.GeoDataFrame,
    output_path: str = "output/eda/dashboard/field_dashboard.html",
) -> None:
    """Create interactive Leaflet map HTML."""
    print("Creating interactive map...")

    properties = []
    for _, row in gdf.iterrows():
        props = {
            "field_id": row["field_id"],
            "state": row["state"],
            "assigned_crop": row["assigned_crop"],
            "area_acres": row["area_acres"],
            "soil_type": row.get("soil_type"),
            "soil_drainage": row.get("soil_drainage"),
            "soil_om_pct": row.get("soil_om_pct"),
            "soil_ph": row.get("soil_ph"),
            "ndvi_peak": row.get("ndvi_peak"),
            "ndvi_mean": row.get("ndvi_mean"),
            "geometry": row.geometry.__geo_interface__,
        }
        properties.append(props)

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {k: v for k, v in p.items() if k != "geometry"},
                "geometry": p["geometry"],
            }
            for p in properties
        ],
    }

    fields_json = json.dumps(geojson)

    n_fields = len(gdf)
    n_corn = len(gdf[gdf["assigned_crop"] == "corn"])

    html = LEAFLET_TEMPLATE.replace("{{fields_json}}", fields_json)
    html = html.replace("{{n_fields}}", str(n_fields))
    html = html.replace("{{n_corn}}", str(n_corn))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)

    print(f"  Saved: {output_path}")
    print(f"  Fields: {n_fields} (corn: {n_corn}, soybeans: {n_fields - n_corn})")


def run_map_generation(
    fields_path: str = "output/fields_50_cornbelt.geojson",
    merged_path: str = "output/eda/merged_eda_data.csv",
    output_path: str = "output/eda/dashboard/field_dashboard.html",
) -> dict:
    """Run full map generation pipeline."""
    print("=" * 60)
    print("Geospatial Map Generation")
    print("=" * 60)

    gdf = load_and_merge_data(fields_path, merged_path)
    create_interactive_map(gdf, output_path)

    summary = {
        "n_fields": len(gdf),
        "n_corn": len(gdf[gdf["assigned_crop"] == "corn"]),
        "n_soybeans": len(gdf[gdf["assigned_crop"] == "soybeans"]),
        "states": gdf["state"].unique().tolist(),
    }

    print("\n" + "=" * 60)
    print("Map Generation Complete")
    print("=" * 60)
    print(f"\nFields: {summary['n_fields']}")
    print(f"Corn: {summary['n_corn']}, Soybeans: {summary['n_soybeans']}")
    print(f"States: {', '.join(summary['states'])}")

    return summary


def main():
    """Run map generation."""
    run_map_generation()


if __name__ == "__main__":
    main()
