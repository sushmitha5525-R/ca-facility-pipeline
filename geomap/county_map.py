"""
geomap/county_map.py

Creates a California county choropleth map showing
number of healthcare facilities per county.

Run with:
    python geomap/county_map.py
"""

import sys
import json
import urllib.request
from pathlib import Path

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import PROC_DATA_DIR, BASE_DIR


def load_county_summary():
    """Load the county summary from PySpark output."""
    path = PROC_DATA_DIR / "spark_county_summary.csv"
    if not path.exists():
        print(f"ERROR: {path} not found — run spark_transform.py first")
        sys.exit(1)

    df = pd.read_csv(path)
    print(f"Loaded county summary: {len(df)} rows")

    # Aggregate total facilities per county
    county_totals = (
        df.groupby("county")["total_facilities"]
        .sum()
        .reset_index()
        .rename(columns={"total_facilities": "total_facilities"})
    )
    county_totals["county"] = county_totals["county"].str.lower().str.strip()
    print(f"Unique counties: {len(county_totals)}")
    return county_totals


def download_california_shapefile():
    """
    Download California county boundaries shapefile from Census Bureau.
    Saved to data/raw/ so it's only downloaded once.
    """
    import zipfile
    import io

    shapefile_dir = BASE_DIR / "data" / "raw" / "ca_counties"

    if shapefile_dir.exists():
        print("California shapefile already downloaded")
        return shapefile_dir

    print("Downloading California county shapefile...")
    url = (
        "https://www2.census.gov/geo/tiger/TIGER2022/COUNTY/"
        "tl_2022_us_county.zip"
    )

    with urllib.request.urlopen(url) as response:
        zip_data = response.read()

    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        z.extractall(shapefile_dir)

    print(f"Shapefile saved to {shapefile_dir}")
    return shapefile_dir


def build_map():
    """Build and save the California county choropleth map."""

    # Load county summary data
    county_totals = load_county_summary()

    # Download and load shapefile
    shapefile_dir = download_california_shapefile()
    shapefile_path = list(shapefile_dir.glob("*.shp"))[0]
    gdf = gpd.read_file(shapefile_path)

    # Filter to California only (STATEFP = '06')
    ca_gdf = gdf[gdf["STATEFP"] == "06"].copy()
    ca_gdf["county"] = ca_gdf["NAME"].str.lower().str.strip()

    print(f"California counties in shapefile: {len(ca_gdf)}")

    # Merge with facility counts
    merged = ca_gdf.merge(county_totals, on="county", how="left")
    merged["total_facilities"] = merged["total_facilities"].fillna(0)

    print(f"Merged rows: {len(merged)}")
    print(f"Counties with data: {(merged['total_facilities'] > 0).sum()}")

    # ── Plot ───────────────────────────────────────────────────
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    merged.plot(
        column="total_facilities",
        ax=ax,
        legend=True,
        cmap="YlOrRd",
        edgecolor="white",
        linewidth=0.5,
        legend_kwds={
            "label": "Number of Licensed Healthcare Facilities",
            "orientation": "horizontal",
            "shrink": 0.6,
            "pad": 0.02,
        },
    )

    # Add county names for top 10
    top10 = merged.nlargest(10, "total_facilities")
    for _, row in top10.iterrows():
        centroid = row.geometry.centroid
        ax.annotate(
            f"{row['NAME']}\n{int(row['total_facilities']):,}",
            xy=(centroid.x, centroid.y),
            fontsize=6,
            ha="center",
            color="black",
        )

    ax.set_title(
        "California Licensed Healthcare Facilities by County",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    ax.set_axis_off()

    # Save
    output_path = BASE_DIR / "data" / "processed" / "ca_facility_map.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nMap saved to {output_path}")
    plt.show()


if __name__ == "__main__":
    print("=" * 55)
    print("CA Facility Pipeline — GeoPandas County Map")
    print("=" * 55)
    build_map()
    print("GeoPandas map complete!")
    print("=" * 55)