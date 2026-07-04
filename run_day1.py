import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s"
)
log = logging.getLogger(__name__)


def run_step(step_num, description, func):
    border = "=" * 55
    print(f"\n{border}")
    print(f"  STEP {step_num}: {description}")
    print(border)

    try:
        result = func()
        print(f"\n  Step {step_num} complete\n")
        return result
    except SystemExit as e:
        log.error(f"Step {step_num} exited with code {e.code}")
        sys.exit(e.code)
    except Exception as e:
        log.error(f"Step {step_num} failed: {e}")
        log.error("Fix the error above and re-run run_day1.py")
        sys.exit(1)


if __name__ == "__main__":

    from ingestion.downloader import download_all
    downloaded = run_step(1, "Download CDPH CSV files", download_all)

    if not downloaded:
        log.error("No files downloaded — check your .env and internet connection")
        sys.exit(1)

    from ingestion.explore import explore_all
    run_step(2, "Explore data (columns, nulls, samples)", explore_all)

    from ingestion.loader import load_all
    success = run_step(3, "Load raw data into PostgreSQL", load_all)

    print("\n" + "=" * 55)
    if success:
        print("  DAY 1 COMPLETE!")
        print("  Your raw tables are live in PostgreSQL.")
        print("  Next: Day 2 — dbt models and transformations.")
    else:
        print("  Day 1 finished with errors.")
        print("  Check the logs/ folder for details.")
    print("=" * 55 + "\n")