#!/usr/bin/env python3
"""NASA POWER weather data analysis for Michigan agricultural fields.

This script analyzes daily weather data from NASA POWER to generate:
- Temperature and precipitation trends
- Growing Degree Days (GDD) calculations
- Seasonal summaries
- Extreme weather statistics
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats


def load_weather_data(csv_path: str) -> pd.DataFrame:
    """Load weather data from NASA POWER CSV export.
    
    Parameters:
        csv_path: Path to weather CSV file
        
    Returns:
        DataFrame with parsed dates and weather columns
    """
    df = pd.read_csv(csv_path, parse_dates=['DATE'])
    df = df.sort_values('DATE')
    return df


def calculate_gdd(df: pd.DataFrame, base_temp: float = 10.0) -> pd.DataFrame:
    """Calculate Growing Degree Days from daily temperature data.
    
    Formula: GDD = ((Tmax + Tmin) / 2) - BaseTemp
    If Tmax > 30°C, cap at 30°C. If Tmin < BaseTemp, use BaseTemp.
    
    Parameters:
        df: Weather DataFrame with T2M_MAX and T2M_MIN columns
        base_temp: Base temperature in Celsius (default: 10°C for corn)
        
    Returns:
        DataFrame with GDD column added
    """
    df = df.copy()
    
    tmax = df['T2M_MAX'].clip(upper=30)
    tmin = df['T2M_MIN'].clip(lower=base_temp)
    
    df['GDD'] = ((tmax + tmin) / 2) - base_temp
    df['GDD'] = df['GDD'].clip(lower=0)
    
    return df


def calculate_degree_days(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Heating Degree Days (HDD) and Cooling Degree Days (CDD).
    
    Parameters:
        df: Weather DataFrame
        
    Returns:
        DataFrame with HDD and CDD columns
    """
    df = df.copy()
    
    df['HDD'] = (18 - df['T2M_MAX']).clip(lower=0)
    df['CDD'] = (df['T2M_MIN'] - 18).clip(lower=0)
    
    return df


def calculate_trend(df: pd.DataFrame, column: str, freq: str = 'YE') -> pd.DataFrame:
    """Calculate linear trend for a given column.
    
    Parameters:
        df: DataFrame with date index
        column: Column name to analyze
        freq: Frequency for resampling ('YE' = yearly, 'ME' = monthly)
        
    Returns:
        DataFrame with trend statistics
    """
    yearly = df.resample(freq)[column].mean()
    yearly = yearly.dropna()
    
    if len(yearly) < 2:
        return None
    
    x = np.arange(len(yearly))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, yearly.values)
    
    result = pd.DataFrame({
        'period': yearly.index,
        'value': yearly.values,
        'trend': slope * x + intercept
    })
    
    result.attrs['slope'] = slope
    result.attrs['r_squared'] = r_value ** 2
    result.attrs['p_value'] = p_value
    
    return result


def seasonal_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate seasonal temperature summaries.
    
    Parameters:
        df: Weather DataFrame
        
    Returns:
        DataFrame with seasonal statistics
    """
    df = df.copy()
    df['month'] = df['DATE'].dt.month
    df['season'] = df['month'].map(lambda m: 
        'Winter' if m in [12, 1, 2] else
        'Spring' if m in [3, 4, 5] else
        'Summer' if m in [6, 7, 8] else 'Fall'
    )
    
    seasonal = df.groupby('season').agg({
        'T2M_MAX': ['mean', 'std'],
        'T2M_MIN': ['mean', 'std'],
        'PRECTOTCORR': ['mean', 'sum', 'std']
    }).round(2)
    
    return seasonal


def extreme_days(df: pd.DataFrame, precip_threshold: float = None) -> dict:
    """Identify extreme weather days.
    
    Parameters:
        df: Weather DataFrame
        precip_threshold: Precipitation percentile for "extreme" (default: 95th)
        
    Returns:
        Dictionary with extreme day statistics
    """
    if precip_threshold is None:
        precip_threshold = df['PRECTOTCORR'].quantile(0.95)
    
    heavy_precip_days = (df['PRECTOTCORR'] > precip_threshold).sum()
    total_days = len(df)
    
    return {
        'heavy_precip_days': heavy_precip_days,
        'heavy_precip_pct': heavy_precip_days / total_days * 100,
        'precip_threshold_95th': precip_threshold,
        'max_temp_days': (df['T2M_MAX'] > 30).sum(),
        'min_temp_days': (df['T2M_MIN'] < 0).sum(),
        'mean_wind': df['WS2M'].mean()
    }


def analyze_weather(csv_path: str, output_dir: str = None) -> dict:
    """Main weather analysis function.
    
    Parameters:
        csv_path: Path to NASA POWER CSV
        output_dir: Optional directory to save results
        
    Returns:
        Dictionary with all analysis results
    """
    print(f"Loading weather data from {csv_path}...")
    df = load_weather_data(csv_path)
    
    print(f"Loaded {len(df)} daily observations")
    print(f"Date range: {df['DATE'].min()} to {df['DATE'].max()}")
    
    df = calculate_gdd(df)
    df = calculate_degree_days(df)
    
    results = {
        'summary': {
            'total_days': len(df),
            'date_range': f"{df['DATE'].min()} to {df['DATE'].max()}",
            'mean_temp': df['T2M'].mean(),
            'mean_precip': df['PRECTOTCORR'].mean(),
            'total_precip': df['PRECTOTCORR'].sum()
        },
        'gdd': {
            'annual': df.resample('YE', on='DATE')['GDD'].sum().to_dict(),
            'growing_season': df[(df['DATE'].dt.month >= 4) & 
                                  (df['DATE'].dt.month <= 9)]['GDD'].sum()
        },
        'trends': {},
        'seasonal': seasonal_summary(df).to_dict(),
        'extremes': extreme_days(df)
    }
    
    temp_trend = calculate_trend(df, 'T2M')
    if temp_trend:
        results['trends']['temperature'] = {
            'slope': temp_trend.attrs['slope'] * 10,
            'r_squared': temp_trend.attrs['r_squared'],
            'p_value': temp_trend.attrs['p_value']
        }
    
    precip_trend = calculate_trend(df, 'PRECTOTCORR')
    if precip_trend:
        results['trends']['precipitation'] = {
            'slope': precip_trend.attrs['slope'] * 10,
            'r_squared': precip_trend.attrs['r_squared'],
            'p_value': precip_trend.attrs['p_value']
        }
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path / 'weather_processed.csv', index=False)
        
        yearly_summary = df.resample('YE', on='DATE').agg({
            'T2M': 'mean',
            'T2M_MAX': 'mean',
            'T2M_MIN': 'mean',
            'PRECTOTCORR': 'sum',
            'GDD': 'sum',
            'HDD': 'sum',
            'CDD': 'sum'
        })
        yearly_summary.to_csv(output_path / 'weather_yearly_summary.csv')
        
        print(f"Results saved to {output_dir}")
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python analyze_weather.py <csv_path> [output_dir]")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    results = analyze_weather(csv_path, output_dir)
    
    print("\n=== Weather Analysis Results ===")
    print(f"\nSummary:")
    print(f"  Mean temperature: {results['summary']['mean_temp']:.1f}°C")
    print(f"  Mean precipitation: {results['summary']['mean_precip']:.1f} mm/day")
    print(f"  Total precipitation: {results['summary']['total_precip']:.0f} mm")
    
    print(f"\nTemperature trend:")
    if 'temperature' in results['trends']:
        t = results['trends']['temperature']
        print(f"  +{t['slope']:.1f}°C/decade (R²={t['r_squared']:.2f}, p={t['p_value']:.2f})")
    
    print(f"\nGDD (base 10°C):")
    for year, gdd in results['gdd']['annual'].items():
        print(f"  {year.year}: {gdd:.0f} degree-days")
