"""Download historical NASA POWER weather data for Michigan fields.

Creates:
- data/michigan_weather_historical.csv

Date range: 2019-01-01 to 2023-12-31 (5-year historical baseline)

Run:
    python scripts/download_historical_weather.py
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

# Historical date range (5 years)
START_DATE = "20190101"
END_DATE = "20231231"


def query_power(lat: float, lon: float, start: str, end: str) -> pd.DataFrame | None:
    """Query NASA POWER API for one location."""
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


def download_historical_for_fields(
    geojson_path: str = "data/michigan_fields.geojson",
    output_csv: str = "data/michigan_weather_historical.csv",
) -> pd.DataFrame:
    """Download historical weather for all fields in a GeoJSON file."""
    with open(geojson_path) as f:
        gj = json.load(f)

    all_dfs = []
    for feature in gj["features"]:
        props = feature["properties"]
        field_id = props.get("field_id", "unknown")

        centroid = shape(feature["geometry"]).centroid
        lat = round(centroid.y, 4)
        lon = round(centroid.x, 4)

        print(f"Querying {field_id} at ({lat}, {lon})... 2019-2023")

        df = query_power(lat, lon, START_DATE, END_DATE)

        if df is not None:
            df.insert(0, "field_id", field_id)
            df.insert(1, "lat", lat)
            df.insert(2, "lon", lon)
            all_dfs.append(df)
            print(f"  Retrieved {len(df)} days of data")

        time.sleep(1)

    result = pd.concat(all_dfs, ignore_index=True)
    result.to_csv(output_csv, index=False)
    print(f"\nSaved {len(result)} rows to {output_csv}")

    return result


if __name__ == "__main__":
    weather = download_historical_for_fields()
    print(f"\nHistorical data summary:")
    print(f"  Date range: {weather['date'].min().date()} to {weather['date'].max().date()}")
    print(f"  Total records: {len(weather)}")
