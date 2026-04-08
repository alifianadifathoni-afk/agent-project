"""EDA utilities for agricultural data analysis."""

import json
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd


def load_fields(path: str = "output/fields_50_cornbelt.geojson") -> gpd.GeoDataFrame:
    """Load field boundaries GeoJSON."""
    return gpd.read_file(path)


def load_soil(path: str = "output/soil_data_50_fields.csv") -> pd.DataFrame:
    """Load soil data."""
    return pd.read_csv(path)


def load_weather(path: str = "output/weather_50_fields_2022_2024.csv") -> pd.DataFrame:
    """Load weather data."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df


def load_cdl(path: str = "output/cdl_50_fields.csv") -> pd.DataFrame:
    """Load CDL crop type data."""
    return pd.read_csv(path)


def load_ndvi(path: str = "output/ndvi_50_fields.csv") -> pd.DataFrame:
    """Load NDVI data."""
    return pd.read_csv(path)


def get_dominant_soil(soil_df: pd.DataFrame) -> pd.DataFrame:
    """Extract dominant soil component per field.

    Takes the soil component with highest comppct_r at shallowest horizon.
    """
    soil_sorted = soil_df.sort_values(
        ["field_id", "comppct_r", "hzdept_r"], ascending=[True, False, True]
    )
    dominant = soil_sorted.groupby("field_id").first().reset_index()
    return dominant


def aggregate_weather(
    weather_df: pd.DataFrame, fields_df: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Aggregate weather data to field-level seasonal summaries.

    Growing season: May-September
    """
    df = weather_df.copy()
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year

    growing_season = df[(df["month"] >= 5) & (df["month"] <= 9)]

    agg = (
        growing_season.groupby("field_id")
        .agg(
            {
                "T2M": "mean",
                "T2M_MAX": "mean",
                "T2M_MIN": "mean",
                "PRECTOTCORR": "sum",
                "ALLSKY_SFC_SW_DWN": "sum",
                "RH2M": "mean",
            }
        )
        .reset_index()
    )

    agg.columns = [
        "field_id",
        "gdd_temp_mean",
        "gdd_temp_max",
        "gdd_temp_min",
        "gdd_precip_total",
        "gdd_solar_total",
        "gdd_humidity_mean",
    ]

    return agg


def calculate_gdd(
    weather_df: pd.DataFrame, base_temp: float = 10.0, cap_temp: float = 30.0
) -> pd.DataFrame:
    """Calculate Growing Degree Days.

    Formula: GDD = max(0, min((T_min + T_max) / 2, cap_temp) - base_temp)
    """
    df = weather_df.copy()
    t_avg = ((df["T2M_MIN"] + df["T2M_MAX"]) / 2).clip(upper=cap_temp)
    df["gdd"] = (t_avg - base_temp).clip(lower=0)
    df["gdd_cumulative"] = df.groupby("field_id")["gdd"].cumsum()
    return df


def export_json(data: Any, path: str) -> None:
    """Export data as JSON."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def export_csv(df: pd.DataFrame, path: str) -> None:
    """Export DataFrame as CSV."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def get_column_descriptions() -> dict[str, str]:
    """Get descriptions for all data columns."""
    return {
        "field_id": "Unique field identifier",
        "state": "US state (IA, IL, IN, MO, OH)",
        "region": "Agricultural region (corn_belt)",
        "crop_name": "Crop type (corn, soybeans)",
        "area_acres": "Field area in acres",
        "centroid_lat": "Field centroid latitude",
        "centroid_lon": "Field centroid longitude",
        "om_r": "Organic matter (%)",
        "ph1to1h2o_r": "Soil pH in water",
        "drainagecl": "Drainage class",
        "claytotal_r": "Clay content (%)",
        "sandtotal_r": "Sand content (%)",
        "silttotal_r": "Silt content (%)",
        "awc_r": "Available water capacity (inches/inch)",
        "dbthirdbar_r": "Bulk density (g/cm³)",
        "cec7_r": "Cation exchange capacity (meq/100g)",
        "T2M": "Mean daily temperature (°C)",
        "T2M_MAX": "Daily maximum temperature (°C)",
        "T2M_MIN": "Daily minimum temperature (°C)",
        "PRECTOTCORR": "Precipitation (mm/day)",
        "ALLSKY_SFC_SW_DWN": "Solar radiation (MJ/m²/day)",
        "RH2M": "Relative humidity (%)",
        "WS10M": "Wind speed (m/s)",
        "ndvi_peak": "Peak NDVI during growing season",
        "ndvi_mean": "Mean NDVI",
    }
