"""Download agricultural field from Illinois Corn Belt.

Creates:
- data/field_illinois_corn.geojson

Usage:
    python scripts/download_illinois_field.py
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).parent.parent / ".opencode" / "skills" / "field-boundaries" / "src")
)

from field_boundaries import download_fields, plot_fields

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"


def main():
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("Downloading 1 field from Illinois Corn Belt...")

    fields = download_fields(
        count=1,
        regions=["corn_belt"],
        crops=["corn"],
        output_path=str(DATA_DIR / "field_illinois_corn.geojson"),
    )

    field = fields.iloc[0]
    print(f"\nField Details:")
    print(f"  Field ID: {field['field_id']}")
    print(f"  Region: {field['region']}")
    print(f"  Crop: {field['crop_name']}")
    print(f"  Area: {field['area_acres']:.2f} acres")
    print(f"  Centroid: {field.geometry.centroid.x:.4f}, {field.geometry.centroid.y:.4f}")

    plot_fields(
        fields,
        title="Illinois Corn Belt Field",
        save_path=str(OUTPUT_DIR / "field_location.png"),
    )
    print(f"\nSaved:")
    print(f"  - {DATA_DIR / 'field_illinois_corn.geojson'}")
    print(f"  - {OUTPUT_DIR / 'field_location.png'}")


if __name__ == "__main__":
    main()
