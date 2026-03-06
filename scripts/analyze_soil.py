#!/usr/bin/env python3
"""USDA SSURGO soil data analysis for Michigan agricultural fields.

This script analyzes soil properties from SSURGO database to generate:
- Soil property distributions (pH, organic matter, texture, CEC)
- Correlation analysis between soil properties
- Soil profile/horizon analysis
- Drainage class summaries
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats


def load_soil_data(csv_path: str) -> pd.DataFrame:
    """Load soil data from SSURGO CSV export.
    
    Parameters:
        csv_path: Path to soil CSV file
        
    Returns:
        DataFrame with soil properties
    """
    df = pd.read_csv(csv_path)
    return df


def calculate_correlation_matrix(df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
    """Calculate correlation matrix for soil properties.
    
    Parameters:
        df: Soil DataFrame
        columns: List of columns to include (default: key soil properties)
        
    Returns:
        Correlation matrix as DataFrame
    """
    if columns is None:
        columns = ['ph', 'om', 'clay', 'sand', 'silt', 'cec', 'awc']
    
    available_cols = [c for c in columns if c in df.columns]
    return df[available_cols].corr()


def soil_profile_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize soil properties by horizon/depth.
    
    Parameters:
        df: Soil DataFrame with horizon information
        
    Returns:
        DataFrame with horizon-level summaries
    """
    if 'horizon' not in df.columns:
        return df.describe()
    
    horizon_summary = df.groupby('horizon').agg({
        'ph': ['mean', 'min', 'max'],
        'om': ['mean', 'min', 'max'],
        'clay': 'mean',
        'cec': 'mean'
    }).round(2)
    
    return horizon_summary


def texture_classification(sand: float, silt: float, clay: float) -> str:
    """Classify soil texture based on USDA triangle.
    
    Parameters:
        sand: Sand percentage
        silt: Silt percentage
        clay: Clay percentage
        
    Returns:
        USDA soil texture class name
    """
    if clay >= 40:
        return 'Clay'
    elif clay >= 27 and sand >= 45:
        return 'Clay loam'
    elif clay >= 27:
        return 'Silty clay'
    elif sand >= 70:
        return 'Sand'
    elif sand >= 50 and silt >= 30:
        return 'Loam'
    elif sand >= 43 and silt >= 30:
        return 'Sandy loam'
    elif silt >= 50:
        return 'Silt loam'
    elif sand >= 70:
        return 'Sandy'
    else:
        return 'Loam'


def field_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Generate field-level soil summaries.
    
    Parameters:
        df: Soil DataFrame
        
    Returns:
        DataFrame with one row per field
    """
    if 'field_id' not in df.columns:
        return df.describe()
    
    field_agg = df.groupby('field_id').agg({
        'ph': 'mean',
        'om': 'mean',
        'clay': 'mean',
        'sand': 'mean',
        'silt': 'mean',
        'cec': 'mean',
        'awc': 'mean',
        'horizon': 'count'
    }).round(2)
    
    field_agg.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col 
                         for col in field_agg.columns]
    field_agg = field_agg.rename(columns={'horizon_count': 'num_horizons'})
    
    return field_agg


def drainage_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze soil properties by drainage class.
    
    Parameters:
        df: Soil DataFrame with drainage_class column
        
    Returns:
        Summary by drainage class
    """
    if 'drainage_class' not in df.columns:
        return None
    
    drainage_summary = df.groupby('drainage_class').agg({
        'ph': ['mean', 'std'],
        'om': ['mean', 'std'],
        'cec': 'mean',
        'awc': 'mean'
    }).round(2)
    
    return drainage_summary


def analyze_soil(csv_path: str, output_dir: str = None) -> dict:
    """Main soil analysis function.
    
    Parameters:
        csv_path: Path to SSURGO CSV
        output_dir: Optional directory to save results
        
    Returns:
        Dictionary with all analysis results
    """
    print(f"Loading soil data from {csv_path}...")
    df = load_soil_data(csv_path)
    
    print(f"Loaded {len(df)} soil horizon records")
    
    key_properties = ['ph', 'om', 'clay', 'sand', 'silt', 'cec', 'awc']
    available = [c for c in key_properties if c in df.columns]
    
    results = {
        'summary': {},
        'correlations': {},
        'by_field': {},
        'by_drainage': None
    }
    
    if available:
        results['summary'] = df[available].describe().to_dict()
        
        corr_matrix = calculate_correlation_matrix(df, available)
        results['correlations'] = corr_matrix.to_dict()
        
        if 'field_id' in df.columns:
            results['by_field'] = field_summary(df).to_dict('index')
        
        if 'drainage_class' in df.columns:
            results['by_drainage'] = drainage_analysis(df).to_dict()
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        corr_matrix.to_csv(output_path / 'soil_correlation_matrix.csv')
        
        if 'field_id' in df.columns:
            field_summary(df).to_csv(output_path / 'soil_field_summary.csv')
        
        print(f"Results saved to {output_dir}")
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python analyze_soil.py <csv_path> [output_dir]")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    results = analyze_soil(csv_path, output_dir)
    
    print("\n=== Soil Analysis Results ===")
    print(f"\nSummary Statistics:")
    for prop, stats_dict in results['summary'].items():
        if isinstance(stats_dict, dict):
            print(f"\n{prop.upper()}:")
            print(f"  Mean: {stats_dict.get('mean', 'N/A'):.2f}")
            print(f"  Std: {stats_dict.get('std', 'N/A'):.2f}")
            print(f"  Range: {stats_dict.get('min', 'N/A'):.2f} - {stats_dict.get('max', 'N/A'):.2f}")
    
    if results['correlations']:
        print(f"\nKey Correlations:")
        corr = pd.DataFrame(results['correlations'])
        for col1 in corr.columns:
            for col2 in corr.columns:
                if col1 < col2:
                    r = corr.loc[col1, col2]
                    if abs(r) > 0.7:
                        print(f"  {col1}-{col2}: r={r:.2f}")
