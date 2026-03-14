#!/usr/bin/env python3
"""
Get NRCS SSURGO soil data for the Michigan field.

This script queries the USDA NRCS Soil Data Access (SDA) REST API
to get real soil properties for the Michigan corn belt field.

Data Source: NRCS Soil Data Access (SDA) REST API
URL: https://sdmdataaccess.sc.egov.usda.gov/

Usage:
    python get_soil_for_michigan_field.py

Output:
    - data/michigan_soil.csv

Soil Properties Retrieved:
    - pH (water)
    - Organic matter
    - Clay/Sand/Silt content
    - Drainage class
    - Available water capacity
    - Cation exchange capacity (CEC)
    - Bulk density
"""

import os
import sys
from pathlib import Path

# Add ssurgo-soil src to path
sys.path.insert(0, str(Path(__file__).parent.parent / ".skills" / "ssurgo-soil" / "src"))

import geopandas as gpd
import pandas as pd


def load_michigan_field() -> gpd.GeoDataFrame:
    """Load the Michigan field from GeoJSON."""
    field_path = Path(__file__).parent.parent / "data" / "michigan_field.geojson"
    field = gpd.read_file(field_path)
    print(f"Loaded field: {field['field_id'].iloc[0]}")
    print(f"Field CRS: {field.crs}")
    return field


def verify_field_crs(field: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Ensure field uses EPSG:4326, convert if needed."""
    print("\n=== FIELD CRS CHECK ===")
    print(f"Current CRS: {field.crs}")
    print(f"EPSG code: {field.crs.to_epsg()}")
    
    if field.crs.to_epsg() != 4326:
        print(f"Converting to EPSG:4326...")
        field = field.to_crs("EPSG:4326")
        print(f"Converted. New CRS: {field.crs}")
    else:
        print("✓ CRS is already EPSG:4326")
    
    print("========================\n")
    return field


def get_soil_data() -> pd.DataFrame:
    """
    Get SSURGO soil data for the Michigan field.
    
    This uses the NRCS Soil Data Access API to query real soil data.
    No API key required.
    
    Returns:
        DataFrame with soil properties
    """
    try:
        from ssurgo_soil import download_soil
    except ImportError:
        print("ERROR: ssurgo_soil module not found")
        print("Trying direct API query...")
        return query_soil_direct()
    
    # Load field
    field = load_michigan_field()
    field = verify_field_crs(field)
    
    # Get soil data
    print("\n=== DOWNLOADING SOIL DATA ===")
    print("Querying NRCS Soil Data Access API...")
    print("This may take 30-60 seconds...")
    
    try:
        soil = download_soil(field, field_id_column="field_id", max_depth_cm=30)
        return soil
    except Exception as e:
        print(f"Error with download_soil: {e}")
        print("Trying direct API query...")
        return query_soil_direct()


def query_soil_direct() -> pd.DataFrame:
    """Direct query to NRCS SDA API using point (centroid)."""
    import requests
    
    # Load field
    field = load_michigan_field()
    field = verify_field_crs(field)
    
    # Use centroid for faster query
    centroid = field.geometry.iloc[0].centroid
    wkt = f"POINT({centroid.x} {centroid.y})"
    field_id = field['field_id'].iloc[0]
    
    print(f"\n=== QUERYING SOIL FOR FIELD: {field_id} ===")
    print(f"Using centroid point: ({centroid.y}, {centroid.x})")
    
    # Build SQL query for SSURGO - point query is faster
    sql = f"""
    SELECT DISTINCT
        mu.mukey,
        mu.muname,
        c.compname,
        c.comppct_r,
        c.drainagecl,
        ch.hzdept_r,
        ch.hzdepb_r,
        ch.om_r,
        ch.ph1to1h2o_r,
        ch.awc_r,
        ch.claytotal_r,
        ch.sandtotal_r,
        ch.silttotal_r,
        ch.dbthirdbar_r,
        ch.cec7_r
    FROM mapunit mu
    INNER JOIN component c ON mu.mukey = c.mukey
    LEFT JOIN chorizon ch ON c.cokey = ch.cokey
    WHERE mu.mukey IN (
        SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84(
            '{wkt}'
        )
    )
    AND (ch.hzdept_r < 30 OR ch.hzdept_r IS NULL)
    ORDER BY c.comppct_r DESC, ch.hzdept_r ASC
    """
    
    # Query API
    url = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
    
    print("Sending request to NRCS SDA API...")
    response = requests.post(
        url,
        data={"query": sql, "format": "JSON"},
        timeout=120
    )
    response.raise_for_status()
    result = response.json()
    
    # Parse results
    if "Table" not in result or not result["Table"]:
        print("No soil data returned")
        return pd.DataFrame()
    
    columns = [
        "mukey", "muname", "compname", "comppct_r", "drainagecl",
        "hzdept_r", "hzdepb_r", "om_r", "ph1to1h2o_r", "awc_r",
        "claytotal_r", "sandtotal_r", "silttotal_r", "dbthirdbar_r", "cec7_r"
    ]
    
    data = []
    for row in result["Table"]:
        data.append(dict(zip(columns, row)))
    
    soil = pd.DataFrame(data)
    soil["field_id"] = field_id
    
    # Convert numeric columns
    numeric_cols = ["comppct_r", "hzdept_r", "hzdepb_r", "om_r", "ph1to1h2o_r", 
                    "awc_r", "claytotal_r", "sandtotal_r", "silttotal_r", 
                    "dbthirdbar_r", "cec7_r"]
    for col in numeric_cols:
        if col in soil.columns:
            soil[col] = pd.to_numeric(soil[col], errors="coerce")
    
    return soil


def verify_soil_data(soil: pd.DataFrame) -> None:
    """Verify soil data and display summary."""
    print("\n=== SOIL DATA VERIFICATION ===")
    print(f"Records retrieved: {len(soil)}")
    print(f"Columns: {list(soil.columns)}")
    
    if not soil.empty:
        print(f"\nUnique soil components: {soil['compname'].nunique()}")
        print(f"Map units (mukey): {soil['mukey'].nunique()}")
        
        # Show dominant soil
        if 'comppct_r' in soil.columns:
            dominant = soil.sort_values('comppct_r', ascending=False).iloc[0]
            print(f"\nDominant soil: {dominant['compname']} ({dominant['comppct_r']}%)")
            print(f"  Drainage: {dominant['drainagecl']}")
            print(f"  pH: {dominant['ph1to1h2o_r']}")
            print(f"  Organic Matter: {dominant['om_r']}%")
            print(f"  Clay: {dominant['claytotal_r']}%")
    else:
        print("\n⚠ No soil data found for this location")
    
    print("=============================\n")


def main():
    """Main function to get soil data."""
    print("=" * 50)
    print("NRCS Soil Data Retrieval")
    print("=" * 50)
    print("\nFetching soil data from NRCS Soil Data Access API...")
    print("Source: https://sdmdataaccess.sc.egov.usda.gov/")
    
    # Get soil data
    soil = get_soil_data()
    
    # Verify
    verify_soil_data(soil)
    
    # Save
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "michigan_soil.csv"
    soil.to_csv(output_path, index=False)
    
    print(f"✓ Saved to: {output_path}")
    print(f"  Total records: {len(soil)}")
    
    print("\n" + "=" * 50)
    print("Soil data retrieval complete!")
    print("=" * 50)
    
    return soil


if __name__ == "__main__":
    soil = main()
