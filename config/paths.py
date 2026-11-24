"""
Kanakkupulla File and Directory Path Management
Implements standard Windows %LOCALAPPDATA% directory structure.
Keeps executable and code completely separate from user financial data.
"""
import os
from pathlib import Path

# LocalAppData standard location
LOCAL_APP_DATA = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
APP_DATA_DIR = LOCAL_APP_DATA / "Kanakkupulla"

# Directories for financial persistence
DATA_DIR = APP_DATA_DIR / "data"
ATTACHMENTS_DIR = APP_DATA_DIR / "attachments"
RECEIPTS_DIR = ATTACHMENTS_DIR / "receipts"
DOCUMENTS_DIR = ATTACHMENTS_DIR / "documents"

BACKUPS_DIR = APP_DATA_DIR / "backups"
BACKUP_DAILY = BACKUPS_DIR / "daily"
BACKUP_WEEKLY = BACKUPS_DIR / "weekly"
BACKUP_MONTHLY = BACKUPS_DIR / "monthly"

LOGS_DIR = APP_DATA_DIR / "logs"
EXPORTS_DIR = APP_DATA_DIR / "exports"
EXPORTS_EXCEL = EXPORTS_DIR / "excel"
EXPORTS_PDF = EXPORTS_DIR / "pdf"
EXPORTS_CSV = EXPORTS_DIR / "csv"

# Ensure all application data directories exist
ALL_DIRS = [
    DATA_DIR, RECEIPTS_DIR, DOCUMENTS_DIR,
    BACKUP_DAILY, BACKUP_WEEKLY, BACKUP_MONTHLY,
    LOGS_DIR, EXPORTS_EXCEL, EXPORTS_PDF, EXPORTS_CSV
]

for d in ALL_DIRS:
    d.mkdir(parents=True, exist_ok=True)

# Main Database File
DB_FILE = DATA_DIR / "kanakkupulla.db"
DB_URL = f"sqlite:///{DB_FILE.as_posix()}"
APPLICATION_LOG_FILE = LOGS_DIR / "application.log"
ERROR_LOG_FILE = LOGS_DIR / "error.log"
