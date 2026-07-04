import os
import sys
import logging
import requests
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_SOURCES, RAW_DATA_DIR, LOG_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "downloader.log"),
    ],
)
log = logging.getLogger(__name__)


def download_file(name, url, save_path):
    log.info(f"Downloading {name} ...")
    log.info(f"  URL : {url}")
    log.info(f"  Save: {save_path}")

    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=4096):
                f.write(chunk)

        file_size_kb = save_path.stat().st_size / 1024
        log.info(f"  Done — {file_size_kb:.1f} KB saved\n")
        return True

    except requests.exceptions.ConnectionError:
        log.error(f"  FAILED — no internet connection or URL unreachable")
        return False
    except requests.exceptions.Timeout:
        log.error(f"  FAILED — request timed out after 60 seconds")
        return False
    except requests.exceptions.HTTPError as e:
        log.error(f"  FAILED — server returned error: {e}")
        return False
    except Exception as e:
        log.error(f"  FAILED — unexpected error: {e}")
        return False


def download_all():
    today = datetime.today().strftime("%Y%m%d")
    results = {}

    log.info("=" * 55)
    log.info("CA Healthcare Facility Pipeline — Day 1 Ingestion")
    log.info("=" * 55)

    for name, url in DATA_SOURCES.items():
        if not url:
            log.warning(f"Skipping {name} — URL not set in .env")
            continue

        filename  = f"{name}_{today}.csv"
        save_path = RAW_DATA_DIR / filename

        if save_path.exists():
            log.info(f"Already downloaded today: {filename} — skipping")
            results[name] = save_path
            continue

        success = download_file(name, url, save_path)
        if success:
            results[name] = save_path

    log.info(f"Download complete: {len(results)}/{len(DATA_SOURCES)} files")
    return results


if __name__ == "__main__":
    downloaded = download_all()

    if len(downloaded) == 0:
        log.error("No files downloaded — check your .env URLs and internet connection")
        sys.exit(1)

    print("\nFiles ready:")
    for name, path in downloaded.items():
        print(f"  {name:25s}  →  {path}")