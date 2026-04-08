"""Run all EDA scripts in sequence.

Usage:
    python scripts/eda/run_all.py
"""

import subprocess
import sys
from pathlib import Path


SCRIPTS = [
    ("01_download_data.py", "Download/generate data layers"),
    ("02_merge_data.py", "Merge data into single dataset"),
    ("03_correlation.py", "Correlation analysis"),
    ("04_crop_compare.py", "Crop comparison (corn vs soybeans)"),
    ("05_dashboard_export.py", "Export dashboard-ready JSON/CSV"),
    ("06_weather_timeseries.py", "Weather time series analysis"),
    ("07_weather_anomalies.py", "Weather anomaly detection"),
]


def run_script(script_name: str, description: str) -> bool:
    """Run a single script and return success status."""
    script_path = Path(__file__).parent / script_name

    print(f"\n{'=' * 60}")
    print(f"Running: {script_name}")
    print(f"Description: {description}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"Error running {script_name}")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"Failed to run {script_name}: {e}")
        return False


def main():
    """Run all EDA scripts."""
    print("=" * 60)
    print("EDA Pipeline - Run All Scripts")
    print("=" * 60)

    results = []

    for script_name, description in SCRIPTS:
        success = run_script(script_name, description)
        results.append((script_name, success))

        if not success:
            print(f"\n⚠️  Failed at {script_name}. Stopping pipeline.")
            break

    print("\n" + "=" * 60)
    print("EDA Pipeline Complete")
    print("=" * 60)

    print("\nResults:")
    for script_name, success in results:
        status = "✓" if success else "✗"
        print(f"  {status} {script_name}")

    all_success = all(success for _, success in results)

    if all_success:
        print("\n✓ All scripts completed successfully!")
        print("\nOutput files:")
        print("  - output/eda/merged_eda_data.csv")
        print("  - output/eda/correlations/*")
        print("  - output/eda/comparisons/*")
        print("  - output/eda/dashboard/*")
        print("  - output/eda/weather/*")
    else:
        print("\n✗ Some scripts failed. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
