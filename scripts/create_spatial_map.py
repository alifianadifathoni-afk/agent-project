"""Create interactive spatial integration map.

Creates:
- output/dashboard_assets/spatial_integration.html

Run:
    python scripts/create_spatial_map.py
"""

import json
import pandas as pd
import geopandas as gpd
from pathlib import Path


def create_interactive_map():
    """Create interactive web map with spatial data integration."""

    DATA_DIR = Path("data")
    OUTPUT_DIR = Path("output/dashboard_assets")
    OUTPUT_HTML = OUTPUT_DIR / "spatial_integration.html"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load spatial data
    print("Loading spatial data...")
    fields = gpd.read_file(DATA_DIR / "michigan_spatial_integration.geojson")

    # Convert any problematic columns to strings (especially datetime)
    for col in fields.columns:
        if fields[col].dtype == "datetime64[ms]":
            fields[col] = fields[col].astype(str)
        elif str(fields[col].dtype) == "object":
            fields[col] = fields[col].astype(str)

    print(f"  Loaded {len(fields)} fields")

    # Calculate map center
    bounds = fields.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Convert to GeoJSON
    geojson_data = json.loads(fields.to_json())

    # Create HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Michigan Corn Fields - Spatial Integration Dashboard</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        #container {{ display: flex; height: 100vh; }}
        
        #sidebar {{
            width: 350px;
            background: #ffffff;
            border-right: 1px solid #ddd;
            padding: 20px;
            overflow-y: auto;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        }}
        
        #sidebar h1 {{
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #1B5E20;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .panel {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .panel h3 {{
            font-size: 0.85em;
            color: #555;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .layer-item {{
            display: flex;
            align-items: center;
            padding: 6px 0;
            cursor: pointer;
        }}
        
        .layer-item input {{
            margin-right: 10px;
        }}
        
        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid #eee;
            font-size: 0.9em;
        }}
        
        .stat-label {{
            color: #666;
        }}
        
        .stat-value {{
            font-weight: 600;
            color: #333;
        }}
        
        #map {{ flex: 1; }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 6px 0;
            font-size: 0.85em;
        }}
        
        .legend-color {{
            width: 24px;
            height: 14px;
            border-radius: 3px;
            margin-right: 10px;
        }}
        
        .info-card {{
            background: white;
            padding: 12px;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            margin-bottom: 8px;
        }}
        
        .info-card h4 {{
            color: #1B5E20;
            margin-bottom: 8px;
            font-size: 1em;
        }}
        
        .color-scale {{
            height: 12px;
            border-radius: 3px;
            margin: 8px 0;
        }}
    </style>
</head>
<body>
    <div id="container">
        <div id="sidebar">
            <h1>🌽 Michigan Corn Fields</h1>
            <p style="color: #666; font-size: 0.9em; margin-bottom: 15px;">
                Spatial Integration Dashboard
            </p>
            
            <div class="panel">
                <h3>Data Layers</h3>
                <div class="layer-item">
                    <input type="checkbox" id="layer-fields" checked onchange="toggleLayer('fields')">
                    <span>Field Boundaries</span>
                </div>
                <div class="layer-item">
                    <input type="checkbox" id="layer-ndvi" checked onchange="toggleLayer('ndvi')">
                    <span>NDVI (Vegetation Index)</span>
                </div>
            </div>
            
            <div class="panel">
                <h3>Field Statistics</h3>
                <div class="stat-row">
                    <span class="stat-label">Total Fields</span>
                    <span class="stat-value">{len(fields)}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Total Area</span>
                    <span class="stat-value">{fields["area_acres"].sum():,.0f} acres</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Avg NDVI</span>
                    <span class="stat-value">{fields["ndvi_mean"].mean():.2f}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Avg Soil pH</span>
                    <span class="stat-value">{fields["soil_ph"].mean():.1f}</span>
                </div>
            </div>
            
            <div class="panel">
                <h3>NDVI Legend</h3>
                <div class="color-scale" style="background: linear-gradient(to right, #8B4513, #FFD700, #9ACD32, #228B22, #006400);"></div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8em; color: #666;">
                    <span>0.0 (Bare)</span>
                    <span>1.0 (Dense)</span>
                </div>
            </div>
        </div>
        
        <div id="map"></div>
    </div>
    
    <script>
        var map = L.map('map').setView([{center_lat:.4f}, {center_lon:.4f}], 8);
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; OpenStreetMap contributors'
        }}).addTo(map);
        
        var fieldData = {json.dumps(geojson_data)};
        
        // NDVI color function
        function getNDVIColor(ndvi) {{
            if (ndvi < 0.3) return '#8B4513';
            if (ndvi < 0.5) return '#DAA520';
            if (ndvi < 0.7) return '#9ACD32';
            if (ndvi < 0.85) return '#228B22';
            return '#006400';
        }}
        
        var layers = {{}};
        
        // NDVI-colored field layer
        layers.fields = L.geoJSON(fieldData, {{
            style: function(feature) {{
                var ndvi = feature.properties.ndvi_mean || 0.5;
                return {{
                    color: '#1B5E20',
                    weight: 2,
                    fillColor: getNDVIColor(ndvi),
                    fillOpacity: 0.7
                }};
            }},
            onEachFeature: function(feature, layer) {{
                var props = feature.properties;
                var popupContent = `
                    <div class="info-card">
                        <h4>📍 ${{props.field_id}}</h4>
                        <div class="stat-row">
                            <span>County:</span>
                            <span>${{props.county}}</span>
                        </div>
                        <div class="stat-row">
                            <span>Area:</span>
                            <span>${{props.area_acres.toFixed(1)}} acres</span>
                        </div>
                        <hr style="margin: 8px 0; border: none; border-top: 1px solid #eee;">
                        <div class="stat-row">
                            <span>🌱 Soil Type:</span>
                            <span>${{props.soil_type}}</span>
                        </div>
                        <div class="stat-row">
                            <span>💧 Drainage:</span>
                            <span>${{props.drainage_class}}</span>
                        </div>
                        <div class="stat-row">
                            <span>📊 Organic Matter:</span>
                            <span>${{props.organic_matter_pct}}%</span>
                        </div>
                        <div class="stat-row">
                            <span>⚗️ Soil pH:</span>
                            <span>${{props.soil_ph}}</span>
                        </div>
                        <hr style="margin: 8px 0; border: none; border-top: 1px solid #eee;">
                        <div class="stat-row">
                            <span>🌿 NDVI Mean:</span>
                            <span style="color: ${{getNDVIColor(props.ndvi_mean)}}; font-weight: bold;">${{props.ndvi_mean.toFixed(3)}}</span>
                        </div>
                        <div class="stat-row">
                            <span>📈 NDVI Range:</span>
                            <span>${{props.ndvi_min.toFixed(3)}} - ${{props.ndvi_max.toFixed(3)}}</span>
                        </div>
                    </div>
                `;
                layer.bindPopup(popupContent);
            }}
        }}).addTo(map);
        
        function toggleLayer(name) {{
            var checkbox = document.getElementById('layer-' + name);
            if (checkbox.checked) {{
                map.addLayer(layers[name]);
            }} else {{
                map.removeLayer(layers[name]);
            }}
        }}
        
        // Fit bounds to data
        map.fitBounds(layers.fields.getBounds(), {{padding: [50, 50]}});
    </script>
</body>
</html>"""

    with open(OUTPUT_HTML, "w") as f:
        f.write(html)

    print(f"\nCreated interactive map: {OUTPUT_HTML}")
    print("Open this file in any web browser")


if __name__ == "__main__":
    create_interactive_map()
