import sys
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import DB_URL, RAW_DATA_DIR, LOG_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "loader.log"),
    ],
)
log = logging.getLogger(__name__)

TABLE_MAP = {
    "facility_locations": "raw_facility_locations",
    "across_time":        "raw_across_time_summary",
}


def get_engine():
    try:
        engine = create_engine(DB_URL, echo=False)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log.info("Connected to PostgreSQL successfully")
        return engine
    except Exception as e:
        log.error(f"Could not connect to PostgreSQL: {e}")
        log.error("Check your .env DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        sys.exit(1)


def find_latest_file(name):
    matches = sorted(RAW_DATA_DIR.glob(f"{name}_*.csv"))
    return matches[-1] if matches else None


def clean_column_names(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
        .str.replace("(", "")
        .str.replace(")", "")
    )
    return df


def load_file_to_postgres(engine, name, table_name):
    path = find_latest_file(name)
    if path is None:
        log.warning(f"No file for '{name}' — run downloader.py first")
        return 0

    log.info(f"\nLoading {path.name}  →  {table_name}")

    try:
        df = pd.read_csv(path, low_memory=False)
        log.info(f"  Read {len(df):,} rows, {len(df.columns)} columns")

        df = clean_column_names(df)
        df["loaded_at"] = datetime.utcnow()

        df.to_sql(
            name=table_name,
            con=engine,
            schema="public",
            if_exists="replace",
            index=False,
            chunksize=1000,
            method="multi",
        )

        log.info(f"  Loaded {len(df):,} rows into public.{table_name}")
        return len(df)

    except Exception as e:
        log.error(f"  FAILED to load {name}: {e}")
        return 0


def validate_load(engine):
    log.info("\n" + "=" * 55)
    log.info("VALIDATION SUMMARY")
    log.info("=" * 55)

    checks_passed = 0
    checks_total  = 0

    with engine.connect() as conn:
        for name, table in TABLE_MAP.items():
            checks_total += 1
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM public.{table}")
            )
            row_count = result.scalar()

            if row_count > 0:
                log.info(f"  {table:<40} {row_count:>8,} rows  PASS")
                checks_passed += 1
            else:
                log.error(f"  {table:<40} {'0':>8} rows  FAIL")

    log.info(f"\n  {checks_passed}/{checks_total} validation checks passed")
    return checks_passed == checks_total


def load_all():
    log.info("=" * 55)
    log.info("CA Facility Pipeline — Loading raw data to PostgreSQL")
    log.info("=" * 55)

    engine = get_engine()
    total_rows = 0

    for name, table in TABLE_MAP.items():
        rows = load_file_to_postgres(engine, name, table)
        total_rows += rows

    log.info(f"\nTotal rows loaded across all tables: {total_rows:,}")

    all_passed = validate_load(engine)
    engine.dispose()
    return all_passed


if __name__ == "__main__":
    success = load_all()
    sys.exit(0 if success else 1)