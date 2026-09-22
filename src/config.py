from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_FILE = RAW_DIR / "online_retail.xlsx"
SQLITE_FILE = PROCESSED_DIR / "smarterp.db"
MODEL_VERSION = 2
DATASET_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"

for directory in (RAW_DIR, PROCESSED_DIR):
    directory.mkdir(parents=True, exist_ok=True)
