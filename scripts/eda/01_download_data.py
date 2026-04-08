"""Download and generate all agricultural data layers for EDA.

This script generates the following data layers:
- Field boundaries (50 fields in Corn Belt)
- SSURGO soil data
- NASA POWER weather data (2022-2024)
- CDL crop type data
- NDVI data

Usage:
    python scripts/eda/01_download_data.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import export_csv, export_json

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon


def generate_fields(count: int = 50, output_path: str = "output/fields_50_cornbelt.geojson"):
    """Generate synthetic field boundaries in Corn Belt."""
    np.random.seed(42)

    CORNBELT_STATES = {
        "IA": {"lat_range": (40.5, 43.5), "lon_range": (-96.5, -90.0)},
        "IL": {"lat_range": (37.5, 42.5), "lon_range": (-91.5, -87.5)},
        "IN": {"lat_range": (37.5, 41.5), "lon_range": (-88.5, -84.5)},
        "OH": {"lat_range": (38.5, 42.0), "lon_range": (-84.5, -80.5)},
        "MO": {"lat_range": (36.5, 40.5), "lon_range": (-95.5, -89.0)},
    }

    CROPS = ["corn", "soybeans"]

    # Change to scripts/eda/output for relative paths
    if not os.path.isabs(output_path):
        output_path = os.path.join(os.path.dirname(__file__), "output", output_path)

    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    data = {
        "field_id": [],
        "state": [],
        "region": [],
        "crop_name": [],
        "area_acres": [],
        "centroid_lat": [],
        "centroid_lon": [],
        "geometry": [],
    }

    for i in range(count):
        state = np.random.choice(list(CORNBELT_STATES.keys()))
        state_info = CORNBELT_STATES[state]
        crop = np.random.choice(CROPS)

        center_lat = np.random.uniform(*state_info["lat_range"])
        center_lon = np.random.uniform(*state_info["lon_range"])
        size = np.random.uniform(0.002, 0.015)

        coords = [
            (center_lon - size, center_lat - size),
            (center_lon + size, center_lat - size),
            (center_lon + size, center_lat + size),
            (center_lon - size, center_lat + size),
            (center_lon - size, center_lat - size),
        ]

        polygon = Polygon(coords)
        area_acres = polygon.area * 24710538

        data["field_id"].append(f"CB_{state}_{i + 1:03d}")
        data["state"].append(state)
        data["region"].append("corn_belt")
        data["crop_name"].append(crop)
        data["area_acres"].append(round(area_acres, 2))
        data["centroid_lat"].append(round(center_lat, 6))
        data["centroid_lon"].append(round(center_lon, 6))
        data["geometry"].append(polygon)

    gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    gdf.to_file(output_path, driver="GeoJSON")

    print(f"✓ Generated {len(gdf)} fields -> {output_path}")
    print(f"  Fields by state: {gdf.groupby('state').size().to_dict()}")
    print(f"  Fields by crop: {gdf.groupby('crop_name').size().to_dict()}")

    return gdf


def generate_soil(
    fields_gdf: gpd.GeoDataFrame, output_path: str = "output/soil_data_50_fields.csv"
):
    """Generate synthetic SSURGO soil data."""
    np.random.seed(42)

    SOIL_TYPES = {
        "Clarion": {
            "om_range": (2.5, 4.5),
            "ph_range": (6.0, 7.2),
            "drainage": "Well drained",
            "clay_range": (18, 28),
        },
        "Webster": {
            "om_range": (3.0, 5.5),
            "ph_range": (6.2, 7.5),
            "drainage": "Poorly drained",
            "clay_range": (20, 32),
        },
        "Nicollet": {
            "om_range": (3.5, 5.0),
            "ph_range": (6.5, 7.3),
            "drainage": "Somewhat poorly drained",
            "clay_range": (22, 30),
        },
        "Canisteo": {
            "om_range": (2.5, 4.0),
            "ph_range": (6.0, 7.0),
            "drainage": "Poorly drained",
            "clay_range": (24, 35),
        },
        "Brockhaven": {
            "om_range": (1.5, 3.0),
            "ph_range": (5.8, 6.8),
            "drainage": "Well drained",
            "clay_range": (15, 25),
        },
        "Cisne": {
            "om_range": (2.0, 3.5),
            "ph_range": (6.2, 7.0),
            "drainage": "Poorly drained",
            "clay_range": (25, 38),
        },
        "Blount": {
            "om_range": (2.0, 3.5),
            "ph_range": (6.5, 7.2),
            "drainage": "Somewhat poorly drained",
            "clay_range": (20, 30),
        },
        "Pewamo": {
            "om_range": (3.0, 5.0),
            "ph_range": (6.8, 7.5),
            "drainage": "Poorly drained",
            "clay_range": (30, 42),
        },
        "Hoytville": {
            "om_range": (2.5, 4.0),
            "ph_range": (6.5, 7.3),
            "drainage": "Poorly drained",
            "clay_range": (25, 35),
        },
        "Miami": {
            "om_range": (2.0, 3.5),
            "ph_range": (6.2, 7.2),
            "drainage": "Well drained",
            "clay_range": (18, 28),
        },
    }

    soil_list = []

    for idx, row in fields_gdf.iterrows():
        field_id = row["field_id"]

        soil_type = np.random.choice(list(SOIL_TYPES.keys()))
        soil_props = SOIL_TYPES[soil_type]

        for horizon in [0, 15, 30]:
            om = np.random.uniform(*soil_props["om_range"])
            if horizon > 0:
                om *= 1 - horizon / 100

            ph = np.random.uniform(*soil_props["ph_range"]) + np.random.uniform(-0.2, 0.2)
            ph = max(4.5, min(8.5, ph))

            clay = np.random.uniform(*soil_props["clay_range"])
            sand = 100 - clay - np.random.uniform(10, 30)
            silt = 100 - clay - sand

            soil_list.append(
                {
                    "field_id": field_id,
                    "mukey": f"MU_{hash(field_id) % 10000:04d}",
                    "muname": soil_type,
                    "compname": soil_type,
                    "comppct_r": 100 - horizon // 10,
                    "drainagecl": soil_props["drainage"],
                    "hzdept_r": horizon,
                    "hzdepb_r": horizon + 15 if horizon < 30 else 60,
                    "om_r": round(om, 2),
                    "ph1to1h2o_r": round(ph, 2),
                    "awc_r": round(np.random.uniform(0.15, 0.22), 3),
                    "claytotal_r": round(clay, 1),
                    "sandtotal_r": round(sand, 1),
                    "silttotal_r": round(silt, 1),
                    "dbthirdbar_r": round(np.random.uniform(1.3, 1.7), 2),
                    "cec7_r": round(np.random.uniform(12, 25), 1),
                    "lat": row["centroid_lat"],
                    "lon": row["centroid_lon"],
                }
            )

    df = pd.DataFrame(soil_list)
    export_csv(df, output_path)

    print(f"✓ Generated {len(df)} soil records -> {output_path}")

    return df


def download_weather(
    fields_gdf: gpd.GeoDataFrame, output_path: str = "output/weather_50_fields_2022_2024.csv"
):
    """Download NASA POWER weather data for field centroids."""
    try:
        import requests
    except ImportError:
        print("✗ requests not installed. Run: uv pip install requests")
        return None

    API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
    PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN", "RH2M", "WS10M"]

    unique_coords = fields_gdf[["field_id", "centroid_lat", "centroid_lon"]].drop_duplicates()

    all_weather = []
    start = "20220101"
    end = "20241231"

    for idx, row in unique_coords.iterrows():
        field_id = row["field_id"]
        lat = row["centroid_lat"]
        lon = row["centroid_lon"]

        try:
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
                timeout=120,
            )
            if resp.status_code != 200:
                print(f"  Error {resp.status_code} for {field_id}")
                continue

            data = resp.json()
            param_data = data["properties"]["parameter"]
            first_param = list(param_data.keys())[0]
            dates = list(param_data[first_param].keys())

            for d in dates:
                row_data = {"field_id": field_id, "date": pd.to_datetime(d, format="%Y%m%d")}
                for p in PARAMS:
                    val = param_data.get(p, {}).get(d, -999.0)
                    row_data[p] = val if val != -999.0 else None
                all_weather.append(row_data)

            print(f"  Downloaded weather for {field_id}")
            time.sleep(1)

        except Exception as e:
            print(f"  Error for {field_id}: {e}")

    if all_weather:
        df = pd.DataFrame(all_weather)
        df = df.sort_values(["field_id", "date"]).reset_index(drop=True)

        field_coords = fields_gdf[["field_id", "centroid_lat", "centroid_lon"]].drop_duplicates()
        df = df.merge(field_coords, on="field_id", how="left")

        cols = ["field_id", "centroid_lat", "centroid_lon", "date"] + PARAMS
        df = df[cols]

        export_csv(df, output_path)
        print(f"✓ Downloaded {len(df)} weather records -> {output_path}")

        return df

    return None


def generate_cdl(fields_gdf: gpd.GeoDataFrame, output_path: str = "output/cdl_50_fields.csv"):
    """Generate CDL crop type data."""
    np.random.seed(42)

    CROP_CODES = {1: "Corn", 5: "Soybeans", 24: "Winter Wheat", 36: "Alfalfa"}
    years = [2022, 2023, 2024]

    cdl_records = []

    for idx, row in fields_gdf.iterrows():
        field_id = row["field_id"]
        assigned_crop = row["crop_name"]

        for year in years:
            if assigned_crop == "corn":
                crop_code = 1 if year == 2023 else np.random.choice([1, 5], p=[0.7, 0.3])
            else:
                crop_code = 5 if year == 2023 else np.random.choice([5, 1], p=[0.7, 0.3])

            cdl_records.append(
                {
                    "field_id": field_id,
                    "year": year,
                    "crop_code": crop_code,
                    "crop_name": CROP_CODES.get(crop_code, f"Code_{crop_code}"),
                    "dominant_pct": round(np.random.uniform(85, 98), 1),
                    "total_pixels": int(np.random.randint(50, 500)),
                    "state": row["state"],
                }
            )

    df = pd.DataFrame(cdl_records)
    export_csv(df, output_path)

    print(f"✓ Generated {len(df)} CDL records -> {output_path}")

    return df


def generate_ndvi(
    fields_gdf: gpd.GeoDataFrame,
    cdl_df: pd.DataFrame,
    output_path: str = "output/ndvi_50_fields.csv",
):
    """Generate NDVI data."""
    np.random.seed(42)

    cdl_2024 = cdl_df[cdl_df["year"] == 2024].copy()

    ndvi_records = []

    for idx, row in cdl_2024.iterrows():
        field_id = row["field_id"]
        crop = row["crop_name"]

        if crop == "Corn":
            ndvi_growing = np.random.uniform(0.5, 0.85)
            ndvi_peak = np.random.uniform(0.7, 0.92)
            ndvi_mature = np.random.uniform(0.35, 0.6)
            ndvi_harvest = np.random.uniform(0.15, 0.35)
        else:
            ndvi_growing = np.random.uniform(0.4, 0.7)
            ndvi_peak = np.random.uniform(0.6, 0.85)
            ndvi_mature = np.random.uniform(0.3, 0.55)
            ndvi_harvest = np.random.uniform(0.1, 0.3)

        ndvi_records.append(
            {
                "field_id": field_id,
                "year": 2024,
                "ndvi_early_season": round(ndvi_growing, 3),
                "ndvi_peak": round(ndvi_peak, 3),
                "ndvi_mature": round(ndvi_mature, 3),
                "ndvi_harvest": round(ndvi_harvest, 3),
                "ndvi_mean": round((ndvi_growing + ndvi_peak + ndvi_mature + ndvi_harvest) / 4, 3),
                "ndvi_std": round(np.random.uniform(0.08, 0.2), 3),
            }
        )

    df = pd.DataFrame(ndvi_records)
    export_csv(df, output_path)

    print(f"✓ Generated {len(df)} NDVI records -> {output_path}")

    return df


def main():
    """Run all data download/generation steps."""
    print("=" * 60)
    print("EDA Data Download Pipeline")
    print("=" * 60)

    print("\n[1/5] Generating field boundaries...")
    fields_gdf = generate_fields()

    print("\n[2/5] Generating soil data...")
    soil_df = generate_soil(fields_gdf)

    print("\n[3/5] Downloading weather data...")
    weather_df = download_weather(fields_gdf)

    print("\n[4/5] Generating CDL crop type data...")
    cdl_df = generate_cdl(fields_gdf)

    print("\n[5/5] Generating NDVI data...")
    ndvi_df = generate_ndvi(fields_gdf, cdl_df)

    print("\n" + "=" * 60)
    print("Data download complete!")
    print("=" * 60)
    print(f"\nOutput files:")
    print(f"  - output/fields_50_cornbelt.geojson")
    print(f"  - output/soil_data_50_fields.csv")
    print(f"  - output/weather_50_fields_2022_2024.csv")
    print(f"  - output/cdl_50_fields.csv")
    print(f"  - output/ndvi_50_fields.csv")


if __name__ == "__main__":
    main()
