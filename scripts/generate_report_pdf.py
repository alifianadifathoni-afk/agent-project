#!/usr/bin/env python3
"""
Generate PDF Report from Soil Health Dashboard Visualizations
===============================================================
Combines all dashboard PNG images into a professional multi-page PDF report.

Fixed version with proper image scaling and page layouts.
"""

import os
from datetime import datetime
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.gridspec as gridspec
import pandas as pd


def create_cover_page(fig):
    """Create the cover page with title and summary."""
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Title
    ax.text(
        0.5,
        0.75,
        "SOIL HEALTH & SUSTAINABILITY",
        fontsize=32,
        fontweight="bold",
        ha="center",
        va="center",
        color="#2E7D32",
    )
    ax.text(
        0.5,
        0.63,
        "ANALYSIS REPORT",
        fontsize=28,
        fontweight="bold",
        ha="center",
        va="center",
        color="#2E7D32",
    )

    # Subtitle
    ax.text(
        0.5,
        0.48,
        "Iowa Corn Belt Field Cluster",
        fontsize=18,
        ha="center",
        va="center",
        color="#555555",
    )
    ax.text(
        0.5,
        0.42,
        "30 Fields Comprehensive Assessment",
        fontsize=14,
        ha="center",
        va="center",
        color="#777777",
    )

    # Divider line
    ax.axhline(y=0.34, xmin=0.2, xmax=0.8, color="#2E7D32", linewidth=3)

    # Key Stats Box
    stats_text = (
        "ANALYSIS SUMMARY\n\n"
        "• 30 Agricultural Fields Analyzed\n"
        "• USDA NASS & NRCS SSURGO Data\n"
        "• 6 Key Health Metrics Evaluated\n"
        "• Erosion Risk Assessment Included\n"
        "• Carbon Storage Potential Calculated"
    )
    ax.text(
        0.5,
        0.18,
        stats_text,
        fontsize=11,
        ha="center",
        va="center",
        fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#F5F5F5", edgecolor="#2E7D32", linewidth=2),
    )

    # Date
    ax.text(
        0.5,
        0.03,
        f"Generated: {datetime.now().strftime('%B %Y')}",
        fontsize=10,
        ha="center",
        va="center",
        color="#999999",
    )


def create_executive_summary(fig):
    """Create executive summary page with key findings."""
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Title
    ax.text(0.05, 0.95, "EXECUTIVE SUMMARY", fontsize=20, fontweight="bold", color="#2E7D32")
    ax.axhline(y=0.92, xmin=0.05, xmax=0.25, color="#2E7D32", linewidth=2)

    # Key findings
    findings = [
        ("Overall Soil Health Score", "67.2 / 100 (Moderate)"),
        ("Average Organic Matter", "3.98% (Below 4% target)"),
        ("Average pH Level", "6.53 (Within optimal range 6.0-7.0)"),
        ("Average CEC", "20.6 meq/100g (Good nutrient retention)"),
        ("Carbon Storage Potential", "16.5 Mg/ha (Moderate)"),
        ("Erosion Risk", "57% Low, 43% Moderate, 0% High"),
    ]

    y_pos = 0.82
    for label, value in findings:
        ax.text(0.05, y_pos, f"• {label}:", fontsize=12, fontweight="bold", va="top")
        ax.text(0.38, y_pos, value, fontsize=12, va="top", color="#333333")
        y_pos -= 0.075

    # Recommendations section
    ax.text(0.05, 0.48, "KEY RECOMMENDATIONS", fontsize=16, fontweight="bold", color="#2E7D32")
    ax.axhline(y=0.45, xmin=0.05, xmax=0.25, color="#2E7D32", linewidth=2)

    recommendations = [
        "1. Focus soil building efforts on bottom-ranked fields (F028, F001, F006)",
        "2. Implement cover crops to increase organic matter content",
        "3. Apply variable rate lime based on pH spatial variation",
        "4. Establish buffer strips on fields with moderate erosion risk",
        "5. Target precision nutrient application on high-CEC fields",
    ]

    y_pos = 0.40
    for rec in recommendations:
        ax.text(0.05, y_pos, rec, fontsize=11, va="top", color="#444444")
        y_pos -= 0.07

    # Data source note
    ax.text(
        0.05,
        0.03,
        "Data Sources: USDA NASS Crop Sequence Boundaries (2023), NRCS SSURGO via Soil Data Access API",
        fontsize=8,
        color="#999999",
        style="italic",
    )


def add_image_page(pdf, image_path, title, caption=None, page_size=(11, 8.5)):
    """Add a full-page image to the PDF with proper scaling."""
    img = Image.open(image_path)
    width, height = img.size

    page_width, page_height = page_size
    margin = 0.6
    title_space = 0.6
    caption_space = 0.3 if caption else 0

    available_width = page_width - 2 * margin
    available_height = page_height - 2 * margin - title_space - caption_space

    # Proper scaling: convert pixels to inches (assuming 100 DPI for PNG)
    img_width_inch = width / 100
    img_height_inch = height / 100

    # Scale to fit within available space
    scale_w = available_width / img_width_inch
    scale_h = available_height / img_height_inch
    scale = min(scale_w, scale_h)

    fig_width = img_width_inch * scale
    fig_height = img_height_inch * scale

    fig = plt.figure(figsize=(page_width, page_height))
    ax = fig.add_subplot(111)
    ax.imshow(img)
    ax.axis("off")

    # Add title at top
    fig.suptitle(title, fontsize=18, fontweight="bold", y=0.97, color="#2E7D32")

    # Add caption if provided
    if caption:
        fig.text(0.5, 0.03, caption, fontsize=10, ha="center", style="italic", color="#666666")

    # Save with padding
    pdf.savefig(fig, bbox_inches="tight", pad_inches=0.4)
    plt.close()


def add_two_images_page(pdf, image1_path, image2_path, title1, title2):
    """Add two images side by side with proper layout."""
    img1 = Image.open(image1_path)
    img2 = Image.open(image2_path)

    # Use landscape for side-by-side
    fig = plt.figure(figsize=(14, 8))  # Wider for two images

    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.15, left=0.05, right=0.95)

    # Left image
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.imshow(img1)
    ax1.axis("off")
    ax1.set_title(title1, fontsize=14, fontweight="bold", color="#2E7D32", pad=10)

    # Right image
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.imshow(img2)
    ax2.axis("off")
    ax2.set_title(title2, fontsize=14, fontweight="bold", color="#2E7D32", pad=10)

    fig.suptitle(
        "SUSTAINABILITY ASSESSMENT", fontsize=16, fontweight="bold", y=0.98, color="#2E7D32"
    )

    pdf.savefig(fig, bbox_inches="tight", pad_inches=0.4)
    plt.close()


def create_field_data_table(pdf, csv_path):
    """Create a table page with field data."""
    df = pd.read_csv(csv_path)

    cols = [
        "field_id",
        "rank",
        "soil_health_score",
        "om_avg",
        "ph_avg",
        "cec_avg",
        "carbon_storage_mg_ha",
        "erosion_risk",
        "drainage_class",
    ]
    df_table = df[cols].copy()

    df_table.columns = [
        "Field",
        "Rank",
        "Health\nScore",
        "OM%",
        "pH",
        "CEC",
        "Carbon\n(Mg/ha)",
        "Erosion\nRisk",
        "Drainage",
    ]
    df_table = df_table.sort_values("Rank")

    fig = plt.figure(figsize=(11, 8.5))
    ax = fig.add_subplot(111)
    ax.axis("off")

    ax.text(
        0.5,
        0.98,
        "FIELD RANKINGS - COMPLETE DATA",
        fontsize=14,
        fontweight="bold",
        ha="center",
        color="#2E7D32",
    )

    table = ax.table(
        cellText=df_table.values,
        colLabels=df_table.columns,
        loc="center",
        cellLoc="center",
        colColours=["#2E7D32"] * len(df_table.columns),
    )

    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 1.5)

    for i in range(len(df_table.columns)):
        table[(0, i)].set_text_props(color="white", fontweight="bold")

    for i in range(1, len(df_table) + 1):
        for j in range(len(df_table.columns)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor("#F5F5F5")

    pdf.savefig(fig, bbox_inches="tight", pad_inches=0.3)
    plt.close()


def generate_pdf_report():
    """Main function to generate the complete PDF report."""
    print("Generating PDF Report (Fixed Version)...")

    output_dir = "output/dashboard_assets"
    pdf_path = "output/soil_health_report.pdf"

    required_images = [
        "soil_health_metrics.png",
        "sustainability_scorecard.png",
        "soil_nutrients_radar.png",
        "field_rankings.png",
        "summary_statistics.png",
    ]

    for img in required_images:
        if not os.path.exists(f"{output_dir}/{img}"):
            print(f"Warning: {img} not found!")

    with PdfPages(pdf_path) as pdf:
        # Page 1: Cover (Portrait)
        print("  - Creating cover page...")
        fig = plt.figure(figsize=(8.5, 11))
        create_cover_page(fig)
        pdf.savefig(fig, bbox_inches="tight", pad_inches=0.4)
        plt.close()

        # Page 2: Executive Summary (Portrait)
        print("  - Creating executive summary...")
        fig = plt.figure(figsize=(8.5, 11))
        create_executive_summary(fig)
        pdf.savefig(fig, bbox_inches="tight", pad_inches=0.4)
        plt.close()

        # Page 3: Main Dashboard (Landscape - wide dashboard fits better)
        print("  - Adding main dashboard...")
        add_image_page(
            pdf,
            f"{output_dir}/soil_health_metrics.png",
            "MAIN DASHBOARD - Soil Health Overview",
            "Multi-panel visualization of key soil health metrics",
            page_size=(14, 10),
        )

        # Page 4: Scorecard + Radar (Landscape - wide layout for two images)
        print("  - Adding sustainability scorecard...")
        add_two_images_page(
            pdf,
            f"{output_dir}/sustainability_scorecard.png",
            f"{output_dir}/soil_nutrients_radar.png",
            "Sustainability Scorecard",
            "Nutrient Metrics Radar",
        )

        # Page 5: Field Rankings (Landscape)
        print("  - Adding field rankings...")
        add_image_page(
            pdf,
            f"{output_dir}/field_rankings.png",
            "FIELD RANKINGS - Top 15 Fields",
            "Detailed ranking table with all key metrics",
            page_size=(11, 8.5),
        )

        # Page 6: Summary Statistics (Landscape)
        print("  - Adding summary statistics...")
        add_image_page(
            pdf,
            f"{output_dir}/summary_statistics.png",
            "DISTRIBUTION ANALYSIS - Statistical Summaries",
            "Histograms showing distribution of key metrics",
            page_size=(14, 10),
        )

        # Page 7: Complete Data Table (Landscape)
        print("  - Adding complete data table...")
        create_field_data_table(pdf, "data/soil_erosion_carbon_analysis.csv")

    print(f"\n✓ PDF Report saved to: {pdf_path}")
    print(f"  Total pages: 7")
    return pdf_path


if __name__ == "__main__":
    generate_pdf_report()
