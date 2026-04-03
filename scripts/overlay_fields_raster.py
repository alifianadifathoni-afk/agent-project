"""Overlay field boundaries with Red band, NIR band, and NDVI rasters.

This script:
1. Loads field boundaries from GeoJSON
2. Acquires Landsat imagery (real via USGS API or synthetic for demo)
3. Clips bands to field extent
4. Calculates NDVI
5. Generates PNG visualizations

Usage:
    python scripts/overlay_fields_raster.py

Requirements:
    - Real data: USGS_USERNAME and USGS_PASSWORD in .env
    - Demo data: No credentials needed (uses synthetic rasters)
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.plot import show
from shapely.geometry import mapping


PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def load_fields(fields_path: str = "data/field_illinois_corn.geojson") -> gpd.GeoDataFrame:
    """Load field boundaries from GeoJSON."""
    fields = gpd.read_file(fields_path)
    print(f"Loaded {len(fields)} field(s)")
    for idx, field in fields.iterrows():
        field_id = field.get("field_id", f"field_{idx}")
        crop = field.get("crop_name", "unknown")
        area = field.get("area_acres", 0)
        print(f"  {field_id}: {crop}, {area:.1f} acres")
    return fields


def check_usgs_credentials() -> bool:
    """Check if USGS credentials are available."""
    username = os.environ.get("USGS_USERNAME")
    password = os.environ.get("USGS_PASSWORD")
    return bool(username and password)


def search_landsat_scenes(
    fields: gpd.GeoDataFrame,
    start_date: str = "2024-06-01",
    end_date: str = "2024-08-31",
    cloud_cover_max: float = 20.0,
) -> list:
    """Search Landsat scenes for field bounding box."""
    from landsatxplore.api import API

    bbox = fields.total_bounds
    print(f"Searching Landsat scenes for bbox: {bbox}")
    print(f"  Date range: {start_date} to {end_date}")
    print(f"  Max cloud cover: {cloud_cover_max}%")

    username = os.environ["USGS_USERNAME"]
    password = os.environ["USGS_PASSWORD"]

    api = API(username, password)

    try:
        scenes = api.search(
            dataset="landsat_ot_c2_l2",
            bbox=(bbox[1], bbox[0], bbox[3], bbox[2]),
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=cloud_cover_max,
        )
        print(f"Found {len(scenes)} scene(s)")

        if scenes:
            for scene in scenes[:5]:
                print(f"  - {scene['display_id']}: {scene['cloud_cover']}% cloud")

        return scenes
    finally:
        api.logout()


def download_landsat_bands(
    scene: dict,
    bands: list[str],
    output_dir: Path,
) -> dict:
    """Download Landsat bands for a scene."""
    from landsatxplore.earthexplorer import EarthExplorer

    username = os.environ["USGS_USERNAME"]
    password = os.environ["USGS_PASSWORD"]

    ee = EarthExplorer(username, password)
    entity_id = scene["entity_id"]
    display_id = scene["display_id"]

    print(f"Downloading scene: {display_id}")

    output_dir.mkdir(parents=True, exist_ok=True)
    ee.download(entity_id, output_dir=str(output_dir))

    ee.logout()

    band_files = {}
    for band in bands:
        pattern = f"*_SR_{band}.TIF"
        matches = list(output_dir.glob(pattern))
        if matches:
            band_files[band] = str(matches[0])
            print(f"  Found {band}: {matches[0].name}")

    return band_files


def generate_synthetic_bands(
    fields: gpd.GeoDataFrame,
    output_dir: Path,
) -> dict:
    """Generate synthetic Red and NIR bands for demonstration."""
    output_dir.mkdir(parents=True, exist_ok=True)

    field = fields.iloc[0]
    field_id = field.get("field_id", "FIELD_0001")

    bounds = field.geometry.bounds
    width = 100
    height = 100

    res_x = (bounds[2] - bounds[0]) / width
    res_y = (bounds[3] - bounds[1]) / height

    transform = rasterio.transform.from_origin(bounds[0], bounds[3], res_x, res_y)

    base_profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "crs": "EPSG:4326",
        "transform": transform,
        "dtype": "float32",
    }

    np.random.seed(42)

    red = np.random.uniform(1000, 8000, (height, width)).astype("float32")
    red += 2000 * np.sin(np.linspace(0, 4 * np.pi, width)).reshape(1, -1)

    nir = np.random.uniform(8000, 20000, (height, width)).astype("float32")
    nir += 3000 * np.sin(np.linspace(0, 4 * np.pi, width)).reshape(1, -1)

    red_path = output_dir / f"{field_id}_SR_B4_EPSG4326.tif"
    nir_path = output_dir / f"{field_id}_SR_B5_EPSG4326.tif"

    with rasterio.open(red_path, "w", **base_profile) as dst:
        dst.write(red, 1)
    print(f"Generated synthetic Red band: {red_path}")

    with rasterio.open(nir_path, "w", **base_profile) as dst:
        dst.write(nir, 1)
    print(f"Generated synthetic NIR band: {nir_path}")

    return {
        "B4": str(red_path),
        "B5": str(nir_path),
    }


def clip_band_to_field(
    band_path: str,
    field: gpd.GeoDataFrame,
    output_path: str,
) -> str:
    """Clip a raster band to field boundary."""
    field_geom = [mapping(field.geometry)]

    with rasterio.open(band_path) as src:
        out_image, out_transform = mask(src, field_geom, crop=True, nodata=0)
        out_meta = src.meta.copy()

    out_meta.update(
        {
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "compress": "lzw",
        }
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, "w", **out_meta) as dst:
        dst.write(out_image[0], 1)

    print(f"Clipped band saved: {output_path}")
    return output_path


def calculate_ndvi(red_path: str, nir_path: str, output_path: str) -> str:
    """Calculate NDVI from Red and NIR bands."""
    with rasterio.open(red_path) as red_src:
        red = red_src.read(1).astype("float32")
        profile = red_src.profile.copy()

    with rasterio.open(nir_path) as nir_src:
        nir = nir_src.read(1).astype("float32")

    denominator = nir + red
    ndvi = np.where(denominator > 0, (nir - red) / denominator, np.nan)

    profile.update(
        dtype="float32",
        count=1,
        compress="lzw",
        nodata=np.nan,
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(ndvi, 1)

    print(f"NDVI saved: {output_path}")
    print(f"  min={np.nanmin(ndvi):.3f} max={np.nanmax(ndvi):.3f} mean={np.nanmean(ndvi):.3f}")
    return output_path


def plot_band_overlay(
    raster_path: str,
    fields: gpd.GeoDataFrame,
    title: str,
    cmap: str,
    output_path: str,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
) -> None:
    """Plot raster with field boundary overlay."""
    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor("white")

    with rasterio.open(raster_path) as src:
        data = src.read(1)
        valid_data = data[~np.isnan(data)]
        bounds = src.bounds
        extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

        if vmin is None:
            vmin = np.min(valid_data)
        if vmax is None:
            vmax = np.max(valid_data)

        im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, extent=extent)
        ax.set_xlim(bounds.left, bounds.right)
        ax.set_ylim(bounds.bottom, bounds.top)

        cbar = plt.colorbar(im, ax=ax, shrink=0.6)
        cbar.set_label("Reflectance", fontsize=12)

    fields.plot(ax=ax, facecolor="none", edgecolor="yellow", linewidth=2)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved map: {output_path}")


def plot_ndvi(fields: gpd.GeoDataFrame, ndvi_path: str, output_path: str) -> None:
    """Plot NDVI with field boundary and colorbar."""
    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor("white")

    with rasterio.open(ndvi_path) as src:
        data = src.read(1)
        bounds = src.bounds
        extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

        im = ax.imshow(data, cmap="RdYlGn", vmin=-0.2, vmax=1.0, extent=extent)
        ax.set_xlim(bounds.left, bounds.right)
        ax.set_ylim(bounds.bottom, bounds.top)

        cbar = plt.colorbar(im, ax=ax, shrink=0.6)
        cbar.set_label("NDVI", fontsize=12)

    fields.plot(ax=ax, facecolor="none", edgecolor="blue", linewidth=2)

    ax.set_title("NDVI - Vegetation Health Index", fontsize=14, fontweight="bold")
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved NDVI map: {output_path}")


def plot_combined_workflow_3x2(
    red_path: str,
    nir_path: str,
    ndvi_path: str,
    fields: gpd.GeoDataFrame,
    output_path: str,
    field_info: dict = None,
) -> None:
    """Create combined 3x2 workflow figure with data panel.

    Layout:
    +------------------------+------------------------+
    |    Red Band (B4)       |    NIR Band (B5)       |
    +------------------------+------------------------+
    |    NDVI Choropleth     |    Data Statistics     |
    +------------------------+------------------------+
    |    NDVI Histogram      |    Metadata / Legend  |
    +------------------------+------------------------+
    """
    fig, axes = plt.subplots(3, 2, figsize=(16, 14))
    fig.patch.set_facecolor("white")

    field = fields.iloc[0]
    field_id = field.get("field_id", "FIELD_0001")
    crop = field.get("crop_name", "Unknown")
    area = field.get("area_acres", 0)

    # Row 1, Col 1: Red Band (B4)
    with rasterio.open(red_path) as src:
        red_data = src.read(1)
        red_valid = red_data[~np.isnan(red_data)]
        red_vmin = np.min(red_valid)
        red_vmax = np.max(red_valid)
        red_bounds = src.bounds
        red_extent = [red_bounds.left, red_bounds.right, red_bounds.bottom, red_bounds.top]

        im_red = axes[0, 0].imshow(
            red_data, cmap="Reds", vmin=red_vmin, vmax=red_vmax, extent=red_extent
        )
        axes[0, 0].set_xlim(red_bounds.left, red_bounds.right)
        axes[0, 0].set_ylim(red_bounds.bottom, red_bounds.top)

        cbar_red = plt.colorbar(im_red, ax=axes[0, 0], shrink=0.6)
        cbar_red.set_label("Reflectance", fontsize=10)

    fields.plot(ax=axes[0, 0], facecolor="none", edgecolor="yellow", linewidth=2)
    axes[0, 0].set_title("Red Band (B4)", fontsize=12, fontweight="bold")
    axes[0, 0].set_xlabel("Longitude", fontsize=10)
    axes[0, 0].set_ylabel("Latitude", fontsize=10)

    # Row 1, Col 2: NIR Band (B5)
    with rasterio.open(nir_path) as src:
        nir_data = src.read(1)
        nir_valid = nir_data[~np.isnan(nir_data)]
        nir_vmin = np.min(nir_valid)
        nir_vmax = np.max(nir_valid)
        nir_bounds = src.bounds
        nir_extent = [nir_bounds.left, nir_bounds.right, nir_bounds.bottom, nir_bounds.top]

        im_nir = axes[0, 1].imshow(
            nir_data, cmap="gray", vmin=nir_vmin, vmax=nir_vmax, extent=nir_extent
        )
        axes[0, 1].set_xlim(nir_bounds.left, nir_bounds.right)
        axes[0, 1].set_ylim(nir_bounds.bottom, nir_bounds.top)

        cbar_nir = plt.colorbar(im_nir, ax=axes[0, 1], shrink=0.6)
        cbar_nir.set_label("Reflectance", fontsize=10)

    fields.plot(ax=axes[0, 1], facecolor="none", edgecolor="yellow", linewidth=2)
    axes[0, 1].set_title("NIR Band (B5)", fontsize=12, fontweight="bold")
    axes[0, 1].set_xlabel("Longitude", fontsize=10)
    axes[0, 1].set_ylabel("Latitude", fontsize=10)

    # Row 2, Col 1: NDVI Choropleth
    with rasterio.open(ndvi_path) as src:
        ndvi_data = src.read(1)
        ndvi_valid = ndvi_data[~np.isnan(ndvi_data)]
        ndvi_bounds = src.bounds
        ndvi_extent = [ndvi_bounds.left, ndvi_bounds.right, ndvi_bounds.bottom, ndvi_bounds.top]

        im = axes[1, 0].imshow(ndvi_data, cmap="RdYlGn", vmin=-0.2, vmax=1.0, extent=ndvi_extent)
        axes[1, 0].set_xlim(ndvi_bounds.left, ndvi_bounds.right)
        axes[1, 0].set_ylim(ndvi_bounds.bottom, ndvi_bounds.top)

        cbar = plt.colorbar(im, ax=axes[1, 0], shrink=0.6)
        cbar.set_label("NDVI", fontsize=10)

    fields.plot(ax=axes[1, 0], facecolor="none", edgecolor="blue", linewidth=2)
    axes[1, 0].set_title("NDVI - Vegetation Index", fontsize=12, fontweight="bold")
    axes[1, 0].set_xlabel("Longitude", fontsize=10)
    axes[1, 0].set_ylabel("Latitude", fontsize=10)

    # Row 2, Col 2: Data Statistics Table
    axes[1, 1].axis("off")

    data_source = "Synthetic (Demo)" if not check_usgs_credentials() else "USGS Landsat 8/9"

    table_data = [
        ["Field ID", field_id],
        ["Crop Type", crop],
        ["Area (acres)", f"{area:.1f}"],
        ["", ""],
        ["Red Band Range", f"{np.min(red_valid):.0f} - {np.max(red_valid):.0f}"],
        ["Red Band Mean", f"{np.mean(red_valid):.1f}"],
        ["", ""],
        ["NIR Band Range", f"{np.min(nir_valid):.0f} - {np.max(nir_valid):.0f}"],
        ["NIR Band Mean", f"{np.mean(nir_valid):.1f}"],
        ["", ""],
        ["NDVI Min", f"{np.min(ndvi_valid):.3f}"],
        ["NDVI Max", f"{np.max(ndvi_valid):.3f}"],
        ["NDVI Mean", f"{np.mean(ndvi_valid):.3f}"],
        ["NDVI Std Dev", f"{np.std(ndvi_valid):.3f}"],
        ["NDVI Median", f"{np.median(ndvi_valid):.3f}"],
    ]

    table = axes[1, 1].table(
        cellText=table_data,
        colWidths=[0.4, 0.6],
        loc="upper left",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.4)

    for i in range(3):
        for j in range(2):
            cell = table[(i, j)]
            if j == 0:
                cell.set_facecolor("#E8E8E8")
                cell.set_text_props(weight="bold")

    axes[1, 1].set_title("Field Statistics & Data Summary", fontsize=12, fontweight="bold", pad=20)

    # Row 3, Col 1: NDVI Histogram
    ndvi_hist = ndvi_valid[(ndvi_valid >= -0.2) & (ndvi_valid <= 1.0)]
    if len(ndvi_hist) > 0:
        axes[2, 0].hist(ndvi_hist, bins=20, color="green", alpha=0.7, edgecolor="darkgreen")
        axes[2, 0].set_xlabel("NDVI", fontsize=10)
        axes[2, 0].set_ylabel("Frequency", fontsize=10)
        axes[2, 0].set_title("NDVI Distribution", fontsize=12, fontweight="bold")
        axes[2, 0].axvline(
            np.mean(ndvi_valid),
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Mean: {np.mean(ndvi_valid):.3f}",
        )
        axes[2, 0].legend(loc="upper right", fontsize=9)
        axes[2, 0].grid(True, alpha=0.3)

    # Row 3, Col 2: Metadata / Legend
    axes[2, 1].axis("off")

    metadata_text = f"""Data Source: {data_source}

Date Range: 2024-06 to 2024-08

Processing Steps:
• Field boundary loaded from GeoJSON
• Rasters clipped to field extent
• NDVI calculated: (NIR - Red) / (NIR + Red)
• Statistics computed per field

NDVI Scale Reference:
• -0.2 to 0.0: Water / Bare soil
• 0.0 to 0.2: Sparse vegetation
• 0.2 to 0.5: Crops / Grassland
• 0.5 to 0.8: Dense vegetation
• 0.8 to 1.0: Dense forest"""

    axes[2, 1].text(
        0.05,
        0.95,
        metadata_text,
        transform=axes[2, 1].transAxes,
        fontsize=10,
        verticalalignment="top",
        fontfamily="monospace",
        bbox=dict(boxstyle="round", facecolor="lightgray", alpha=0.3),
    )

    fig.suptitle(
        f"Field Boundary Overlay Analysis - {field_id}", fontsize=16, fontweight="bold", y=0.98
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved combined workflow figure (3x2): {output_path}")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved combined workflow figure: {output_path}")


def main():
    """Main workflow for field overlay with rasters."""
    print("=" * 60)
    print("Field Boundary Overlay with Red, NIR, and NDVI Rasters")
    print("=" * 60)

    OUTPUT_DIR.mkdir(exist_ok=True)

    fields = load_fields()

    field = fields.iloc[0]
    field_id = field.get("field_id", "FIELD_0001")

    if check_usgs_credentials():
        print("\n[Option 1] USGS credentials found - using real Landsat data")
        print("=" * 60)

        scenes = search_landsat_scenes(fields)

        if scenes:
            best_scene = sorted(scenes, key=lambda s: s["cloud_cover"])[0]
            print(f"\nBest scene: {best_scene['display_id']} ({best_scene['cloud_cover']}% cloud)")

            landsat_dir = DATA_DIR / "landsat"
            band_files = download_landsat_bands(best_scene, ["B4", "B5"], landsat_dir)

            if band_files.get("B4") and band_files.get("B5"):
                red_path = band_files["B4"]
                nir_path = band_files["B5"]
            else:
                print("ERROR: Band files not found, falling back to synthetic")
                use_synthetic = True
        else:
            print("WARNING: No scenes found, falling back to synthetic data")
            use_synthetic = True
    else:
        print("\n[Option 2] No USGS credentials - generating synthetic rasters")
        print("=" * 60)
        use_synthetic = True

    if use_synthetic or not check_usgs_credentials():
        print("\nGenerating synthetic bands for demonstration...")
        band_files = generate_synthetic_bands(fields, DATA_DIR / "landsat")
        red_path = band_files["B4"]
        nir_path = band_files["B5"]

    clipped_dir = DATA_DIR / "landsat" / "clipped"
    clipped_dir.mkdir(parents=True, exist_ok=True)

    print("\nClipping bands to field boundary...")
    clipped_red = str(clipped_dir / f"{field_id}_B4_clipped.tif")
    clipped_nir = str(clipped_dir / f"{field_id}_B5_clipped.tif")

    clip_band_to_field(red_path, field, clipped_red)
    clip_band_to_field(nir_path, field, clipped_nir)

    print("\nCalculating NDVI...")
    ndvi_path = str(clipped_dir / f"{field_id}_NDVI.tif")
    calculate_ndvi(clipped_red, clipped_nir, ndvi_path)

    print("\nGenerating PNG visualizations...")
    plot_band_overlay(
        clipped_red,
        fields,
        "Red Band (B4) - Field Overlay",
        "Reds",
        str(OUTPUT_DIR / f"{field_id}_red_band.png"),
    )

    plot_band_overlay(
        clipped_nir,
        fields,
        "NIR Band (B5) - Field Overlay",
        "gray",
        str(OUTPUT_DIR / f"{field_id}_nir_band.png"),
    )

    plot_ndvi(fields, ndvi_path, str(OUTPUT_DIR / f"{field_id}_ndvi.png"))

    print("\nGenerating combined 2x2 workflow figure...")
    plot_combined_workflow_3x2(
        clipped_red,
        clipped_nir,
        ndvi_path,
        fields,
        str(OUTPUT_DIR / f"{field_id}_overlay_workflow.png"),
    )

    print("\n" + "=" * 60)
    print("Processing complete!")
    print("=" * 60)
    print(f"\nOutput files in: {OUTPUT_DIR}")
    print(f"  - {field_id}_red_band.png")
    print(f"  - {field_id}_nir_band.png")
    print(f"  - {field_id}_ndvi.png")
    print(f"  - {field_id}_overlay_workflow.png (combined 2x2)")


if __name__ == "__main__":
    main()
