"""Correlation analysis for agricultural data.

Computes correlation matrix, identifies strongest relationships,
creates heatmap visualization, and tests statistical significance.

Usage:
    python scripts/eda/03_correlation.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import load_fields, export_json, export_csv
from utils import get_dominant_soil, load_soil, load_weather, load_ndvi, load_cdl

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path


def compute_correlation_matrix(
    df: pd.DataFrame,
    numeric_cols: list,
    method: str = "pearson",
) -> pd.DataFrame:
    """Compute correlation matrix for numeric columns."""
    valid_cols = [col for col in numeric_cols if col in df.columns]
    corr_matrix = df[valid_cols].corr(method=method)
    return corr_matrix


def find_strongest_correlations(
    corr_matrix: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    """Find strongest correlations (excluding self-correlations)."""
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    correlations = corr_matrix.where(mask).stack().reset_index()
    correlations.columns = ["var1", "var2", "correlation"]
    correlations = correlations.sort_values("correlation", key=abs, ascending=False)
    return correlations.head(top_n)


def test_significance(
    df: pd.DataFrame,
    var1: str,
    var2: str,
    method: str = "pearson",
) -> dict:
    """Test statistical significance of correlation."""
    valid_data = df[[var1, var2]].dropna()

    if len(valid_data) < 3:
        return {"error": "Insufficient data"}

    if method == "pearson":
        corr, p_value = stats.pearsonr(valid_data[var1], valid_data[var2])
    elif method == "spearman":
        corr, p_value = stats.spearmanr(valid_data[var1], valid_data[var2])
    else:
        corr, p_value = stats.kendalltau(valid_data[var1], valid_data[var2])

    return {
        "correlation": round(corr, 4),
        "p_value": round(p_value, 6),
        "significant": p_value < 0.05,
        "n_observations": len(valid_data),
    }


def create_correlation_heatmap(
    corr_matrix: pd.DataFrame,
    output_path: str = "output/eda/correlations/correlation_heatmap.png",
    figsize: tuple = (12, 10),
) -> None:
    """Create correlation heatmap visualization."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize)

    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
        ax=ax,
    )

    ax.set_title("Agricultural Data Correlation Matrix", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"✓ Saved heatmap: {output_path}")


def create_scatter_plot(
    df: pd.DataFrame,
    var1: str,
    var2: str,
    output_path: str,
    title: str = None,
) -> None:
    """Create scatter plot with trend line."""
    valid_data = df[[var1, var2]].dropna()

    if len(valid_data) < 3:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.scatter(valid_data[var1], valid_data[var2], alpha=0.6)

    z = np.polyfit(valid_data[var1], valid_data[var2], 1)
    p = np.poly1d(z)
    x_range = np.linspace(valid_data[var1].min(), valid_data[var1].max(), 100)
    ax.plot(x_range, p(x_range), "r--", alpha=0.8, label="Trend line")

    corr, p_value = stats.pearsonr(valid_data[var1], valid_data[var2])

    ax.set_xlabel(var1)
    ax.set_ylabel(var2)
    ax.set_title(f"{var1} vs {var2}\nr = {corr:.3f}, p = {p_value:.4f}")
    ax.legend()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"  Saved scatter: {output_path}")


def run_correlation_analysis(
    merged_path: str = "output/eda/merged_eda_data.csv",
    output_dir: str = "output/eda/correlations",
) -> dict:
    """Run full correlation analysis pipeline."""
    print("Loading merged data...")
    df = pd.read_csv(merged_path)

    numeric_cols = [
        "area_acres",
        "soil_om_pct",
        "soil_ph",
        "soil_clay_pct",
        "soil_sand_pct",
        "soil_silt_pct",
        "soil_awc",
        "soil_bulk_density",
        "soil_cec",
        "gdd_temp_mean",
        "gdd_temp_max",
        "gdd_temp_min",
        "gdd_precip_total",
        "gdd_solar_total",
        "gdd_humidity_mean",
        "ndvi_peak",
        "ndvi_mean",
        "ndvi_std",
    ]

    valid_cols = [col for col in numeric_cols if col in df.columns]
    print(f"Analyzing {len(valid_cols)} numeric variables...")

    print("\n[1/4] Computing correlation matrix...")
    corr_matrix = compute_correlation_matrix(df, valid_cols)

    corr_matrix_path = f"{output_dir}/correlation_matrix.csv"
    Path(corr_matrix_path).parent.mkdir(parents=True, exist_ok=True)
    corr_matrix.to_csv(corr_matrix_path)
    print(f"  Saved: {corr_matrix_path}")

    print("\n[2/4] Finding strongest correlations...")
    top_corr = find_strongest_correlations(corr_matrix, top_n=15)

    top_corr_path = f"{output_dir}/strongest_correlations.csv"
    top_corr.to_csv(top_corr_path, index=False)
    print(f"  Saved: {top_corr_path}")

    print("\n[3/4] Testing significance of top correlations...")
    significance_results = []
    for _, row in top_corr.head(5).iterrows():
        result = test_significance(df, row["var1"], row["var2"])
        result["var1"] = row["var1"]
        result["var2"] = row["var2"]
        result["correlation"] = row["correlation"]
        significance_results.append(result)

        sig_marker = "✓" if result.get("significant") else "✗"
        print(
            f"  {row['var1']} ↔ {row['var2']}: r={row['correlation']:.3f} p={result.get('p_value', 'N/A')} {sig_marker}"
        )

    sig_path = f"{output_dir}/significance_tests.json"
    export_json(significance_results, sig_path)
    print(f"  Saved: {sig_path}")

    print("\n[4/4] Creating visualizations...")
    create_correlation_heatmap(corr_matrix, f"{output_dir}/correlation_heatmap.png")

    for _, row in top_corr.head(3).iterrows():
        create_scatter_plot(
            df,
            row["var1"],
            row["var2"],
            f"{output_dir}/scatter_{row['var1']}_vs_{row['var2']}.png",
        )

    summary = {
        "n_variables": len(valid_cols),
        "n_significant": sum(1 for r in significance_results if r.get("significant")),
        "top_correlation": {
            "var1": top_corr.iloc[0]["var1"],
            "var2": top_corr.iloc[0]["var2"],
            "correlation": round(top_corr.iloc[0]["correlation"], 3),
        },
    }

    export_json(summary, f"{output_dir}/summary.json")

    return summary


def main():
    """Run correlation analysis."""
    print("=" * 60)
    print("EDA Correlation Analysis")
    print("=" * 60)

    summary = run_correlation_analysis()

    print("\n" + "=" * 60)
    print("Correlation Analysis Complete")
    print("=" * 60)
    print(f"\nVariables analyzed: {summary['n_variables']}")
    print(f"Significant correlations: {summary['n_significant']}/5 tested")
    print(
        f"Top correlation: {summary['top_correlation']['var1']} ↔ {summary['top_correlation']['var2']} ({summary['top_correlation']['correlation']})"
    )


if __name__ == "__main__":
    main()
