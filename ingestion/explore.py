import sys
import logging
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import RAW_DATA_DIR, LOG_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "explore.log"),
    ],
)
log = logging.getLogger(__name__)


def find_latest_file(name):
    matches = sorted(RAW_DATA_DIR.glob(f"{name}_*.csv"))
    if not matches:
        log.warning(f"No file found for '{name}' in {RAW_DATA_DIR}")
        return None
    return matches[-1]


def explore_dataframe(df, name):
    sep = "-" * 55

    print(f"\n{sep}")
    print(f"  DATASET: {name.upper()}")
    print(sep)

    print(f"\n  Rows   : {len(df):,}")
    print(f"  Columns: {len(df.columns)}")

    print(f"\n  {'Column':<35} {'Type':<15} {'Nulls':>8}  {'% Null':>8}")
    print(f"  {'-'*35} {'-'*15} {'-'*8}  {'-'*8}")
    for col in df.columns:
        null_count = df[col].isna().sum()
        null_pct   = null_count / len(df) * 100
        print(f"  {col:<35} {str(df[col].dtype):<15} {null_count:>8,}  {null_pct:>7.1f}%")

    print(f"\n  First 3 rows:")
    pd.set_option("display.max_columns", 6)
    pd.set_option("display.width", 100)
    print(df.head(3).to_string(index=False))

    key_columns = [
        "FACTYPE", "FAC_TYPE", "COUNTY", "LICENSE_STATUS",
        "LICENSESTATE", "TYPE_OF_SERVICE"
    ]
    found = [c for c in key_columns if c in df.columns]
    if found:
        print(f"\n  Unique value counts for key columns:")
        for col in found:
            counts = df[col].value_counts().head(5)
            print(f"\n    {col}:")
            for val, cnt in counts.items():
                print(f"      {str(val):<35} {cnt:>6,}")

    print(f"\n{sep}\n")


def explore_all():
    files_to_explore = [
        "facility_locations",
        "facility_services",
        "across_time",
    ]

    log.info("Starting data exploration...")

    for name in files_to_explore:
        path = find_latest_file(name)
        if path is None:
            log.warning(f"Skipping {name} — run downloader.py first")
            continue

        log.info(f"Loading {path.name} ...")

        try:
            df = pd.read_csv(path, low_memory=False)
            explore_dataframe(df, name)

        except Exception as e:
            log.error(f"Could not read {path}: {e}")

    log.info("Exploration complete")


if __name__ == "__main__":
    explore_all()