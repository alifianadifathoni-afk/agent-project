"""Download NASA POWER weather data for Michigan corn fields.

Creates:
- data/michigan_weather_2024.csv

Date range: 2024-05-01 to 2024-09-30 (growing season)

Run:
    python scripts/download_michigan_weather.py
"""

import json
import time
from pathlib import Path

import pandas as pd
import requests
from shapely.geometry import shape

API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

PARAMS = [
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "PRECTOTCORR",
    "ALLSKY_SFC_SW_DWN",
    "RH2M",
]

# Date range for 2024 growing season
START_DATE = "20240501"
END_DATE = "20240930"


def query_power(lat: float, lon: float, start: str, end: str) -> pd.DataFrame | None:
    """Query NASA POWER API for one location.

    Args:
        lat: Latitude
        lon: Longitude
        start: Start date (YYYYMMDD)
        end: End date (YYYYMMDD)

    Returns:
        DataFrame with daily weather data
    """
    resp = requests.get(
        API_URL,
        params={
            "parameters": ",".join(PARAMS),
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": start,
            "end": end,
            "format": "JSON",
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    param_data = data["properties"]["parameter"]
    first_param = list(param_data.keys())[0]
    dates = list(param_data[first_param].keys())

    records = []
    for d in dates:
        row = {"date": pd.to_datetime(d, format="%Y%m%d")}
        for p in PARAMS:
            val = param_data.get(p, {}).get(d, -999.0)
            row[p] = val if val != -999.0 else None
        records.append(row)

    return pd.DataFrame(records)


def download_weather_for_fields(
    geojson_path: str = "data/michigan_fields.geojson",
    output_csv: str = "data/michigan_weather_2024.csv",
) -> pd.DataFrame:
    """Download weather for all fields in a GeoJSON file.

    Args:
        geojson_path: Path to field boundaries GeoJSON
        output_csv: Path to save weather CSV

    Returns:
        DataFrame with weather data for all fields
    """
    with open(geojson_path) as f:
        gj = json.load(f)

    all_dfs = []
    for feature in gj["features"]:
        props = feature["properties"]
        field_id = props.get("field_id", "unknown")

        # Get field centroid
        centroid = shape(feature["geometry"]).centroid
        lat = round(centroid.y, 4)
        lon = round(centroid.x, 4)

        print(f"Querying {field_id} at ({lat}, {lon})...")

        df = query_power(lat, lon, START_DATE, END_DATE)

        if df is not None:
            df.insert(0, "field_id", field_id)
            df.insert(1, "lat", lat)
            df.insert(2, "lon", lon)
            all_dfs.append(df)
            print(f"  Retrieved {len(df)} days of data")

        time.sleep(1)  # Courtesy delay between API calls

    result = pd.concat(all_dfs, ignore_index=True)

    # Save to CSV
    result.to_csv(output_csv, index=False)
    print(f"\nSaved {len(result)} rows to {output_csv}")

    return result


if __name__ == "__main__":
    weather = download_weather_for_fields()

    # Verify datetime format
    print(f"\nDate column dtype: {weather['date'].dtype}")
    print(f"Sample dates:\n{weather['date'].head()}")

    # Show summary
    print(f"\nData summary:")
    print(f"  Fields: {weather['field_id'].nunique()}")
    print(f"  Date range: {weather['date'].min()} to {weather['date'].max()}")
    print(f"  Total records: {len(weather)}")
