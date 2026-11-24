"""
Database Backup & Restore Service:
Provides manual and automated SQLite database backups with timestamped archives and restore capability.
"""
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from config.settings import DB_PATH, BACKUPS_DIR
from database.connection import SessionLocal
from database.models import AuditLog

class BackupService:
    @staticmethod
    def create_backup(custom_destination_dir: Path = BACKUPS_DIR) -> Tuple[bool, str, Path]:
        try:
            custom_destination_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"kanakkupulla_backup_{timestamp}.db"
            target_path = custom_destination_dir / backup_filename

            # Flush current WAL transactions before copying
            db = SessionLocal()
            try:
                db.execute("PRAGMA wal_checkpoint(FULL);")
                db.commit()
            except Exception:
                pass
            finally:
                db.close()

            shutil.copy2(DB_PATH, target_path)
            return True, f"Backup created successfully: {backup_filename}", target_path
        except Exception as e:
            return False, f"Backup failed: {str(e)}", Path()

    @staticmethod
    def restore_backup(backup_file_path: Path) -> Tuple[bool, str]:
        if not backup_file_path.exists():
            return False, "Selected backup file does not exist"

        try:
            # Create a safety fallback copy of current database first
            safety_copy = DB_PATH.with_suffix(".pre_restore.bak")
            shutil.copy2(DB_PATH, safety_copy)

            # Copy backup to live DB path
            shutil.copy2(backup_file_path, DB_PATH)
            return True, "Database restored successfully. Please restart application to re-initialize."
        except Exception as e:
            return False, f"Restore failed: {str(e)}"

    @staticmethod
    def list_backups() -> List[Path]:
        if not BACKUPS_DIR.exists():
            return []
        return sorted(BACKUPS_DIR.glob("kanakkupulla_backup_*.db"), reverse=True)
