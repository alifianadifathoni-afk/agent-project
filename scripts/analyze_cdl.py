#!/usr/bin/env python3
"""USDA CDL (Cropland Data Layer) crop rotation analysis.

This script analyzes CDL data to generate:
- Crop type distributions by year
- Crop rotation patterns
- Land cover change detection
- Field-level crop histories
"""

import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter


def load_cdl_data(csv_path: str) -> pd.DataFrame:
    """Load CDL data from CSV export.
    
    Parameters:
        csv_path: Path to CDL CSV file
        
    Returns:
        DataFrame with CDL crop codes
    """
    df = pd.read_csv(csv_path)
    return df


 CDL_CROP_NAMES = {
    1: 'Corn', 12: 'Soybeans', 24: 'Winter Wheat', 27: 'Oats',
    36: 'Alfalfa', 37: 'Other Hay', 43: 'Pasture/Hay', 61: 'Fallow',
    63: 'Forest', 81: 'Clouds/No Data', 82: 'Developed', 83: 'Open Space',
    87: 'Woody Wetlands', 88: 'Nonag/Undefined', 121: 'Developed/Open',
    141: 'Deciduous Forest', 142: 'Evergreen Forest', 143: 'Mixed Forest',
    152: 'Shrubland', 171: 'Grassland/Herbaceous', 190: 'Woody Wetlands',
    204: 'Coarse Wool', 205: 'Fine Wool', 206: 'Lamb/Year'
}


def map_crop_code(code: int) -> str:
    """Map CDL numeric code to crop name.
    
    Parameters:
        code: CDL numeric code
        
    Returns:
        Human-readable crop name
    """
    return CDL_CROP_NAMES.get(code, f'Unknown ({code})')


def get_dominant_crop(row: pd.Series, year_cols: list) -> tuple:
    """Find dominant crop for a field across years.
    
    Parameters:
        row: DataFrame row with year columns
        year_cols: List of year column names
        
    Returns:
        Tuple of (dominant_crop, max_percentage)
    """
    crops = {}
    for col in year_cols:
        if col in row.index:
            crops[row[col]] = crops.get(row[col], 0) + 1
    
    if not crops:
        return None, 0
    
    dominant = max(crops, key=crops.get)
    return map_crop_code(dominant), crops[dominant]


def analyze_rotation_patterns(df: pd.DataFrame, year_cols: list) -> pd.DataFrame:
    """Analyze crop rotation patterns.
    
    Parameters:
        df: CDL DataFrame
        year_cols: List of year column names
        
    Returns:
        DataFrame with rotation analysis
    """
    results = []
    
    for idx, row in df.iterrows():
        field_id = row.get('field_id', f'Field_{idx}')
        crops = [row[col] for col in year_cols if col in row.index]
        
        unique_crops = len(set(crops))
        rotation_type = 'Monoculture' if unique_crops == 1 else \
                        'Simple Rotation' if unique_crops == 2 else \
                        'Complex Rotation'
        
        crop_names = [map_crop_code(c) for c in crops]
        
        results.append({
            'field_id': field_id,
            'unique_crops': unique_crops,
            'rotation_type': rotation_type,
            'crops': ' -> '.join(crop_names[:5])
        })
    
    return pd.DataFrame(results)


def land_cover_summary(df: pd.DataFrame, year_cols: list) -> dict:
    """Summarize land cover distribution by year.
    
    Parameters:
        df: CDL DataFrame
        year_cols: List of year column names
        
    Returns:
        Dictionary with year-wise crop distributions
    """
    summary = {}
    
    for col in year_cols:
        if col not in df.columns:
            continue
            
        crop_counts = df[col].value_counts()
        year = col.replace('cdl_', '').replace('crop_', '')
        
        summary[year] = {
            map_crop_code(code): {
                'count': int(count),
                'pct': round(count / len(df) * 100, 1)
            }
            for code, count in crop_counts.items()
        }
    
    return summary


def detect_changes(df: pd.DataFrame, year_cols: list) -> pd.DataFrame:
    """Detect land cover changes between years.
    
    Parameters:
        df: CDL DataFrame
        year_cols: List of year column names
        
    Returns:
        DataFrame with change detection results
    """
    changes = []
    
    for i in range(len(year_cols) - 1):
        col1, col2 = year_cols[i], year_cols[i + 1]
        
        if col1 not in df.columns or col2 not in df.columns:
            continue
        
        same = (df[col1] == df[col2]).sum()
        changed = len(df) - same
        
        changes.append({
            'period': f'{col1} to {col2}',
            'unchanged': same,
            'changed': changed,
            'change_pct': round(changed / len(df) * 100, 1)
        })
    
    return pd.DataFrame(changes)


def field_crop_history(df: pd.DataFrame, field_id: str, year_cols: list) -> dict:
    """Get complete crop history for a specific field.
    
    Parameters:
        df: CDL DataFrame
        field_id: Field identifier
        year_cols: List of year column names
        
    Returns:
        Dictionary with field crop history
    """
    field = df[df['field_id'] == field_id]
    
    if field.empty:
        return None
    
    field = field.iloc[0]
    history = {}
    
    for col in year_cols:
        if col in field.index:
            year = col.replace('cdl_', '').replace('crop_', '')
            code = field[col]
            history[year] = {
                'code': int(code),
                'crop': map_crop_code(code)
            }
    
    return history


def analyze_cdl(csv_path: str, output_dir: str = None) -> dict:
    """Main CDL analysis function.
    
    Parameters:
        csv_path: Path to CDL CSV
        output_dir: Optional directory to save results
        
    Returns:
        Dictionary with all analysis results
    """
    print(f"Loading CDL data from {csv_path}...")
    df = load_cdl_data(csv_path)
    
    print(f"Loaded {len(df)} field records")
    
    year_cols = [c for c in df.columns if 'cdl_' in c.lower() or 
                 (c.startswith('20') and len(c) == 4)]
    
    results = {
        'land_cover_summary': land_cover_summary(df, year_cols),
        'rotation_patterns': analyze_rotation_patterns(df, year_cols).to_dict('records'),
        'changes': detect_changes(df, year_cols).to_dict('records'),
        'field_histories': {}
    }
    
    if 'field_id' in df.columns:
        for field_id in df['field_id'].unique():
            results['field_histories'][field_id] = field_crop_history(
                df, field_id, year_cols
            )
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        analyze_rotation_patterns(df, year_cols).to_csv(
            output_path / 'cdl_rotation_patterns.csv', index=False
        )
        
        detect_changes(df, year_cols).to_csv(
            output_path / 'cdl_changes.csv', index=False
        )
        
        print(f"Results saved to {output_dir}")
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python analyze_cdl.py <csv_path> [output_dir]")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    results = analyze_cdl(cdl_csv_path, output_dir)
    
    print("\n=== CDL Analysis Results ===")
    print(f"\nCrop Rotation Patterns:")
    for pattern in results['rotation_patterns'][:5]:
        print(f"  {pattern['field_id']}: {pattern['rotation_type']}")
    
    print(f"\nLand Cover Changes:")
    for change in results['changes']:
        print(f"  {change['period']}: {change['changed']} fields ({change['change_pct']}%)")
