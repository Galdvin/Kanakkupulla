"""
Kanakkupulla Configuration & Constants
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
BACKUPS_DIR = BASE_DIR / "backups"
ATTACHMENTS_DIR = DATA_DIR / "attachments"
ASSETS_DIR = BASE_DIR / "assets"

for d in [DATA_DIR, LOGS_DIR, BACKUPS_DIR, ATTACHMENTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

if os.environ.get("TESTING") == "1":
    DB_PATH = DATA_DIR / "test_kanakkupulla.db"
else:
    DB_PATH = DATA_DIR / "kanakkupulla.db"
DB_URL = f"sqlite:///{DB_PATH.as_posix()}"

APP_NAME = "Kanakkupulla"
APP_VERSION = "1.0.0"
DEFAULT_CURRENCY = "INR"
DEFAULT_CURRENCY_SYMBOL = "₹"
DEFAULT_DATE_FORMAT = "%d-%m-%Y"
DEFAULT_DATETIME_FORMAT = "%d-%m-%Y %H:%M:%S"

# Security
SESSION_TIMEOUT_MINUTES = 15
ARGON2_TIME_COST = 2
ARGON2_MEMORY_COST = 65536
ARGON2_PARALLELISM = 2
