"""
spark/spark_transform.py

Uses PySpark to transform the raw facility data.
PySpark is used in real companies to handle millions of rows
efficiently — same logic as pandas but built for big data.

Run with:
    py spark/spark_transform.py
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import RAW_DATA_DIR, PROC_DATA_DIR

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import FloatType


def create_spark_session():
    """Create a local Spark session."""
    spark = (
        SparkSession.builder
        .appName("CA_Healthcare_Facility_Pipeline")
        .master("local[*]")   # use all CPU cores on your machine
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")  # hide verbose Spark logs
    print("Spark session started successfully")
    return spark


def find_latest_file(name):
    matches = sorted(RAW_DATA_DIR.glob(f"{name}_*.csv"))
    return matches[-1] if matches else None


def transform_facility_locations(spark):
    """
    Transform raw facility locations using PySpark.
    Does the same job as dbt staging but at Spark scale.
    """
    path = find_latest_file("facility_locations")
    if not path:
        print("ERROR: facility_locations file not found")
        return None

    print(f"\nLoading {path.name} into Spark...")

    # Read CSV into a Spark DataFrame
    df = spark.read.csv(
        str(path),
        header=True,        # first row is column names
        inferSchema=True,   # auto-detect data types
    )

    print(f"Raw rows: {df.count():,}")
    print(f"Columns: {len(df.columns)}")

    # ── Transformations ────────────────────────────────────────
    transformed = (
        df
        # Remove rows with no facility ID
        .filter(F.col("FACID").isNotNull())

        # Rename and select columns
        .select(
            F.col("FACID").alias("facility_id"),
            F.col("FACNAME").alias("facility_name"),
            F.col("FAC_TYPE_CODE").alias("facility_type"),
            F.lower(F.trim(F.col("COUNTY_NAME"))).alias("county"),
            F.col("ZIP").alias("zip_code"),
            F.col("CITY").alias("city"),
            F.col("ADDRESS").alias("address"),
            F.col("LICENSED_CERTIFIED").alias("license_status"),
            F.col("CAPACITY").cast(FloatType()).alias("capacity"),
            F.col("CONTACT_PHONE_NUMBER").alias("phone"),
            F.col("COUNTY_CODE").alias("county_code"),
        )

        # Standardize license status to uppercase
        .withColumn("license_status", F.upper(F.col("license_status")))

        # Remove duplicates on facility_id
        .dropDuplicates(["facility_id"])

        # Add processing timestamp
        .withColumn("processed_at", F.lit(datetime.utcnow().isoformat()))
    )

    print(f"Transformed rows: {transformed.count():,}")
    return transformed


def compute_county_summary(df):
    """
    Compute facility counts and compliance rate by county.
    This is the Spark version of your dbt mart model.
    """
    summary = (
        df
        .filter(F.col("county").isNotNull())
        .groupBy("county", "facility_type")
        .agg(
            F.count("*").alias("total_facilities"),
            F.count(
                F.when(F.col("license_status") == "LICENSED", 1)
            ).alias("licensed_count"),
            F.round(
                F.count(F.when(F.col("license_status") == "LICENSED", 1))
                * 100.0 / F.count("*"), 2
            ).alias("compliance_rate_pct"),
        )
        .orderBy("county", F.col("total_facilities").desc())
    )
    return summary




def save_to_csv(df, filename):
    """Save Spark DataFrame to processed folder as CSV using pandas."""
    output_path = PROC_DATA_DIR / f"{filename}.csv"
    # Convert Spark DataFrame to pandas then save — avoids Windows Hadoop issue
    df.toPandas().to_csv(output_path, index=False)
    print(f"Saved to {output_path}")

def main():
    print("=" * 55)
    print("CA Facility Pipeline — PySpark Transformation")
    print("=" * 55)

    # Start Spark
    spark = create_spark_session()

    # Transform facility locations
    facilities_df = transform_facility_locations(spark)
    if facilities_df is None:
        sys.exit(1)

    # Show sample
    print("\nSample transformed rows:")
    facilities_df.select(
        "facility_id", "facility_name", "county", "license_status"
    ).show(5, truncate=False)

    # Compute county summary
    print("\nComputing county summary...")
    summary_df = compute_county_summary(facilities_df)

    print("\nTop 10 counties by facility count:")
    summary_df.groupBy("county").agg(
        F.sum("total_facilities").alias("total")
    ).orderBy(F.col("total").desc()).show(10)

    # Save outputs
    print("\nSaving outputs...")
    save_to_csv(facilities_df, "spark_facilities_clean")
    save_to_csv(summary_df, "spark_county_summary")

    spark.stop()
    print("\nPySpark transformation complete!")
    print("=" * 55)


if __name__ == "__main__":
    main()