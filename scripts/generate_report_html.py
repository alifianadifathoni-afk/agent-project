#!/usr/bin/env python3
"""
Generate HTML Report from Soil Health Dashboard Visualizations
================================================================
Creates a single HTML file with embedded images and interactive elements.
"""

import os
from datetime import datetime


def generate_html_report():
    """Generate an interactive HTML report."""
    print("Generating HTML Report...")

    output_dir = "output/dashboard_assets"
    html_path = "output/soil_health_report.html"

    html_content = (
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Soil Health & Sustainability Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header */
        header {
            background: linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            border-radius: 0 0 20px 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        /* Section styling */
        section {
            background: white;
            margin: 20px 0;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.1);
        }
        
        section h2 {
            color: #2E7D32;
            border-bottom: 3px solid #2E7D32;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        /* Stats grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #f8fff8 0%, #e8f5e9 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #2E7D32;
        }
        
        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #2E7D32;
        }
        
        .stat-card .label {
            font-size: 0.9em;
            color: #666;
        }
        
        /* Image containers */
        .image-section {
            margin: 30px 0;
        }
        
        .image-section img {
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .image-caption {
            text-align: center;
            color: #666;
            font-style: italic;
            margin-top: 10px;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 5px;
        }
        
        /* Two column layout */
        .two-col {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        
        @media (max-width: 768px) {
            .two-col {
                grid-template-columns: 1fr;
            }
        }
        
        /* Table styling */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th {
            background: #2E7D32;
            color: white;
            padding: 12px;
            text-align: left;
        }
        
        td {
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        
        tr:nth-child(even) {
            background: #f9f9f9;
        }
        
        tr:hover {
            background: #f0f7f0;
        }
        
        /* Recommendations */
        .recommendations {
            background: #fff3e0;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #ff9800;
        }
        
        .recommendations li {
            margin: 10px 0;
            padding-left: 10px;
        }
        
        /* Footer */
        footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
            margin-top: 40px;
        }
        
        /* Navigation */
        nav {
            background: #1B5E20;
            padding: 15px;
            position: sticky;
            top: 0;
            z-index: 100;
            border-radius: 0 0 10px 10px;
        }
        
        nav a {
            color: white;
            text-decoration: none;
            margin: 0 15px;
            font-weight: 500;
            transition: opacity 0.3s;
        }
        
        nav a:hover {
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <nav>
        <div class="container">
            <a href="#summary">Summary</a>
            <a href="#dashboard">Dashboard</a>
            <a href="#scorecard">Scorecard</a>
            <a href="#rankings">Rankings</a>
            <a href="#statistics">Statistics</a>
        </div>
    </nav>

    <header>
        <div class="container">
            <h1>🌱 Soil Health & Sustainability Report</h1>
            <p>Iowa Corn Belt Field Cluster | 30 Fields Comprehensive Assessment</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Generated: """
        + datetime.now().strftime("%B %Y")
        + """</p>
        </div>
    </header>

    <div class="container">
        <!-- Executive Summary -->
        <section id="summary">
            <h2>📊 Executive Summary</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="value">67.2</div>
                    <div class="label">Overall Health Score</div>
                </div>
                <div class="stat-card">
                    <div class="value">3.98%</div>
                    <div class="label">Average Organic Matter</div>
                </div>
                <div class="stat-card">
                    <div class="value">6.53</div>
                    <div class="label">Average pH Level</div>
                </div>
                <div class="stat-card">
                    <div class="value">20.6</div>
                    <div class="label">Average CEC (meq/100g)</div>
                </div>
                <div class="stat-card">
                    <div class="value">16.5</div>
                    <div class="label">Carbon Storage (Mg/ha)</div>
                </div>
                <div class="stat-card">
                    <div class="value">17</div>
                    <div class="label">Low Erosion Risk Fields</div>
                </div>
            </div>
            
            <div class="recommendations">
                <h3>🎯 Key Recommendations</h3>
                <ul>
                    <li>Focus soil building efforts on bottom-ranked fields (F028, F001, F006)</li>
                    <li>Implement cover crops to increase organic matter content</li>
                    <li>Apply variable rate lime based on pH spatial variation</li>
                    <li>Establish buffer strips on fields with moderate erosion risk</li>
                    <li>Target precision nutrient application on high-CEC fields</li>
                </ul>
            </div>
            
            <p style="margin-top: 20px; color: #666; font-size: 0.9em;">
                <em>Data Sources: USDA NASS Crop Sequence Boundaries (2023), NRCS SSURGO via Soil Data Access API</em>
            </p>
        </section>

        <!-- Main Dashboard -->
        <section id="dashboard">
            <h2>📈 Main Dashboard</h2>
            <div class="image-section">
                <img src="dashboard_assets/soil_health_metrics.png" alt="Soil Health Dashboard">
                <div class="image-caption">Multi-panel dashboard showing key soil health metrics, comparisons, and spatial distribution</div>
            </div>
        </section>

        <!-- Scorecard & Radar -->
        <section id="scorecard">
            <h2>🎯 Sustainability Assessment</h2>
            <div class="two-col">
                <div class="image-section">
                    <img src="dashboard_assets/sustainability_scorecard.png" alt="Sustainability Scorecard">
                    <div class="image-caption">Circular gauge with category breakdown</div>
                </div>
                <div class="image-section">
                    <img src="dashboard_assets/soil_nutrients_radar.png" alt="Nutrient Radar Chart">
                    <div class="image-caption">6-axis radar comparing cluster average vs. top 5 benchmark</div>
                </div>
            </div>
        </section>

        <!-- Field Rankings -->
        <section id="rankings">
            <h2>🏆 Field Rankings</h2>
            <div class="image-section">
                <img src="dashboard_assets/field_rankings.png" alt="Field Rankings">
                <div class="image-caption">Top 15 fields ranked by overall soil health score</div>
            </div>
        </section>

        <!-- Summary Statistics -->
        <section id="statistics">
            <h2>📉 Distribution Analysis</h2>
            <div class="image-section">
                <img src="dashboard_assets/summary_statistics.png" alt="Summary Statistics">
                <div class="image-caption">Statistical distributions of key soil health metrics</div>
            </div>
        </section>

        <!-- Data Table -->
        <section>
            <h2>📋 Complete Field Data</h2>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Field</th>
                            <th>Rank</th>
                            <th>Health Score</th>
                            <th>OM%</th>
                            <th>pH</th>
                            <th>CEC</th>
                            <th>Carbon</th>
                            <th>Erosion Risk</th>
                            <th>Drainage</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    )

    # Add table rows from CSV
    import pandas as pd

    df = pd.read_csv("data/soil_erosion_carbon_analysis.csv")
    for _, row in df.sort_values("rank").iterrows():
        html_content += f"""
                        <tr>
                            <td><strong>{row["field_id"]}</strong></td>
                            <td>{row["rank"]}</td>
                            <td>{row["soil_health_score"]:.1f}</td>
                            <td>{row["om_avg"]:.2f}</td>
                            <td>{row["ph_avg"]:.1f}</td>
                            <td>{row["cec_avg"]:.1f}</td>
                            <td>{row["carbon_storage_mg_ha"]:.1f}</td>
                            <td>{row["erosion_risk"]}</td>
                            <td>{row["drainage_class"]}</td>
                        </tr>
"""

    html_content += (
        """                    </tbody>
                </table>
            </div>
        </section>
    </div>

    <footer>
        <p>📊 Soil Health & Sustainability Report | Iowa Corn Belt Field Cluster | 30 Fields</p>
        <p>Generated: """
        + datetime.now().strftime("%B %d, %Y")
        + """ | Data: USDA NASS & NRCS SSURGO</p>
    </footer>

</body>
</html>"""
    )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✓ HTML Report saved to: {html_path}")
    return html_path


if __name__ == "__main__":
    generate_html_report()
