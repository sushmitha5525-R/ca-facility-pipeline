import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR      = Path(__file__).resolve().parent.parent
RAW_DATA_DIR  = BASE_DIR / os.getenv("RAW_DATA_DIR", "data/raw")
PROC_DATA_DIR = BASE_DIR / os.getenv("PROCESSED_DATA_DIR", "data/processed")
LOG_DIR       = BASE_DIR / os.getenv("LOG_DIR", "logs")

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROC_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "ca_facility_db"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

DB_URL = (
    f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

DATA_SOURCES = {
    "facility_locations": os.getenv("FACILITY_LOCATIONS_URL"),
    "facility_services":  os.getenv("FACILITY_SERVICES_URL"),
    "across_time":        os.getenv("FACILITY_CROSSWALK_URL"),
}

LOCAL_FILES = {
    "facility_locations": RAW_DATA_DIR / "facility_locations.csv",
    "facility_services":  RAW_DATA_DIR / "facility_services.csv",
    "across_time":        RAW_DATA_DIR / "across_time_summary.csv",
}