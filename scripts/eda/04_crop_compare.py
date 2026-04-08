"""Crop comparison analysis - Corn vs Soybeans.

Compares agricultural variables across crop types using statistical tests
and visualizations.

Usage:
    python scripts/eda/04_crop_compare.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import export_json, export_csv, load_fields
from utils import get_dominant_soil, load_soil, load_weather, load_ndvi, load_cdl
from utils import aggregate_weather

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path


def compute_group_statistics(
    df: pd.DataFrame,
    group_col: str,
    value_cols: list,
) -> pd.DataFrame:
    """Compute summary statistics by group."""
    stats_list = []

    for col in value_cols:
        if col not in df.columns:
            continue

        for group_val in df[group_col].unique():
            group_data = df[df[group_col] == group_val][col].dropna()

            stats_list.append(
                {
                    "variable": col,
                    "group": group_val,
                    "n": len(group_data),
                    "mean": round(group_data.mean(), 3),
                    "std": round(group_data.std(), 3),
                    "min": round(group_data.min(), 3),
                    "max": round(group_data.max(), 3),
                    "median": round(group_data.median(), 3),
                }
            )

    return pd.DataFrame(stats_list)


def ttest_two_groups(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    equal_var: bool = False,
) -> dict:
    """Perform independent t-test between two groups."""
    groups = df[group_col].unique()

    if len(groups) != 2:
        return {"error": f"Expected 2 groups, got {len(groups)}"}

    group1_data = df[df[group_col] == groups[0]][value_col].dropna()
    group2_data = df[df[group_col] == groups[1]][value_col].dropna()

    if len(group1_data) < 3 or len(group2_data) < 3:
        return {"error": "Insufficient data for t-test"}

    t_stat, p_value = stats.ttest_ind(group1_data, group2_data, equal_var=equal_var)

    diff = group1_data.mean() - group2_data.mean()
    pct_diff = (diff / group2_data.mean()) * 100 if group2_data.mean() != 0 else 0

    return {
        "group1": groups[0],
        "group2": groups[1],
        "variable": value_col,
        "group1_mean": round(group1_data.mean(), 3),
        "group2_mean": round(group2_data.mean(), 3),
        "difference": round(diff, 3),
        "pct_difference": round(pct_diff, 1),
        "t_statistic": round(t_stat, 3),
        "p_value": round(p_value, 6),
        "significant": p_value < 0.05,
        "group1_n": len(group1_data),
        "group2_n": len(group2_data),
    }


def create_box_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: str,
    title: str = None,
    palette: str = "Set2",
) -> None:
    """Create box plot comparison."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    sns.boxplot(data=df, x=x_col, y=y_col, palette=palette, ax=ax)

    ax.set_title(title or f"{y_col} by {x_col}", fontsize=14, fontweight="bold")
    ax.set_xlabel(x_col.replace("_", " ").title())
    ax.set_ylabel(y_col.replace("_", " ").title())

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"  Saved: {output_path}")


def create_violin_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: str,
    title: str = None,
    palette: str = "Set2",
) -> None:
    """Create violin plot comparison."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    sns.violinplot(data=df, x=x_col, y=y_col, palette=palette, ax=ax)

    ax.set_title(title or f"{y_col} Distribution by {x_col}", fontsize=14, fontweight="bold")
    ax.set_xlabel(x_col.replace("_", " ").title())
    ax.set_ylabel(y_col.replace("_", " ").title())

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"  Saved: {output_path}")


def create_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: str,
    title: str = None,
    aggregation: str = "mean",
) -> None:
    """Create bar chart comparison."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    agg_df = df.groupby(x_col)[y_col].agg(aggregation).reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(agg_df[x_col], agg_df[y_col], color=["#66c2a5", "#fc8d62"])

    ax.set_title(title or f"{y_col} by {x_col}", fontsize=14, fontweight="bold")
    ax.set_xlabel(x_col.replace("_", " ").title())
    ax.set_ylabel(y_col.replace("_", " ").title())

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"  Saved: {output_path}")


def run_crop_comparison(
    merged_path: str = "output/eda/merged_eda_data.csv",
    output_dir: str = "output/eda/comparisons",
) -> dict:
    """Run full crop comparison analysis."""
    print("Loading merged data...")
    df = pd.read_csv(merged_path)

    comparison_vars = [
        "area_acres",
        "soil_om_pct",
        "soil_ph",
        "soil_clay_pct",
        "soil_bulk_density",
        "gdd_temp_mean",
        "gdd_precip_total",
        "gdd_solar_total",
        "ndvi_peak",
        "ndvi_mean",
    ]

    valid_vars = [col for col in comparison_vars if col in df.columns]
    print(f"\nComparing {len(valid_vars)} variables between corn and soybeans...")

    print("\n[1/4] Computing group statistics...")
    group_stats = compute_group_statistics(df, "assigned_crop", valid_vars)

    stats_path = f"{output_dir}/crop_statistics.csv"
    Path(stats_path).parent.mkdir(parents=True, exist_ok=True)
    group_stats.to_csv(stats_path, index=False)
    print(f"  Saved: {stats_path}")

    print("\n[2/4] Running t-tests...")
    ttest_results = []

    for var in valid_vars:
        result = ttest_two_groups(df, "assigned_crop", var)
        if "error" not in result:
            ttest_results.append(result)
            sig = "✓" if result["significant"] else "✗"
            print(
                f"  {var}: corn={result['group1_mean']}, soy={result['group2_mean']}, p={result['p_value']:.4f} {sig}"
            )

    sig_path = f"{output_dir}/ttest_results.json"
    export_json(ttest_results, sig_path)
    print(f"  Saved: {sig_path}")

    print("\n[3/4] Creating visualizations...")
    os.makedirs(f"{output_dir}/boxplots", exist_ok=True)
    os.makedirs(f"{output_dir}/violin", exist_ok=True)

    key_vars = ["ndvi_peak", "soil_om_pct", "gdd_precip_total", "soil_ph"]
    for var in key_vars:
        if var in df.columns:
            create_box_plot(
                df,
                "assigned_crop",
                var,
                f"{output_dir}/boxplots/{var}_boxplot.png",
                title=f"{var.replace('_', ' ').title()} by Crop Type",
            )
            create_violin_plot(
                df,
                "assigned_crop",
                var,
                f"{output_dir}/violin/{var}_violin.png",
                title=f"{var.replace('_', ' ').title()} Distribution by Crop Type",
            )

    print("\n[4/4] Creating summary dashboard...")
    summary = {
        "n_corn": len(df[df["assigned_crop"] == "corn"]),
        "n_soybeans": len(df[df["assigned_crop"] == "soybeans"]),
        "n_significant_differences": sum(1 for r in ttest_results if r["significant"]),
        "variables_tested": len(ttest_results),
        "significant_vars": [r["variable"] for r in ttest_results if r["significant"]],
    }

    summary_path = f"{output_dir}/summary.json"
    export_json(summary, summary_path)
    print(f"  Saved: {summary_path}")

    return summary


def main():
    """Run crop comparison analysis."""
    print("=" * 60)
    print("EDA Crop Comparison Analysis")
    print("=" * 60)

    summary = run_crop_comparison()

    print("\n" + "=" * 60)
    print("Crop Comparison Complete")
    print("=" * 60)
    print(f"\nFields: {summary['n_corn']} corn, {summary['n_soybeans']} soybeans")
    print(
        f"Significant differences: {summary['n_significant_differences']}/{summary['variables_tested']}"
    )
    if summary["significant_vars"]:
        print(f"Significant variables: {', '.join(summary['significant_vars'])}")


if __name__ == "__main__":
    main()
