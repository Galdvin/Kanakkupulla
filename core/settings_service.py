"""
Application Settings & Preferences Service:
Manages runtime configuration, key-value preferences stored in SQLite,
Family Profile updates, and system environment diagnostics.
"""
from typing import Dict, Any, Optional
import sys
import os
import platform
import sqlite3
from pathlib import Path
import sqlalchemy
import PySide6

from database.connection import SessionLocal
from database.models import ApplicationSetting, FamilyProfile, User, FinancialTransaction
from config.settings import (
    DB_PATH, ATTACHMENTS_DIR, APP_NAME, APP_VERSION,
    DEFAULT_CURRENCY, DEFAULT_CURRENCY_SYMBOL, DEFAULT_DATE_FORMAT,
    ARGON2_TIME_COST, ARGON2_MEMORY_COST, ARGON2_PARALLELISM
)

class SettingsService:
    DEFAULT_SETTINGS = {
        "app_currency_symbol": DEFAULT_CURRENCY_SYMBOL,
        "app_currency_code": DEFAULT_CURRENCY,
        "app_date_format": DEFAULT_DATE_FORMAT,
        "theme_mode": "dark",
        "auto_backup_enabled": "true",
        "auto_backup_frequency": "Daily",
        "fiscal_year_start": "April",
        "session_timeout_minutes": "30"
    }

    @staticmethod
    def get_setting(key: str, default: Optional[str] = None) -> str:
        db = SessionLocal()
        try:
            item = db.query(ApplicationSetting).filter_by(key=key).first()
            if item:
                return item.value
            return default if default is not None else SettingsService.DEFAULT_SETTINGS.get(key, "")
        finally:
            db.close()

    @staticmethod
    def set_setting(key: str, value: str) -> bool:
        db = SessionLocal()
        try:
            item = db.query(ApplicationSetting).filter_by(key=key).first()
            if item:
                item.value = str(value)
            else:
                item = ApplicationSetting(key=key, value=str(value))
                db.add(item)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    @staticmethod
    def get_all_settings() -> Dict[str, str]:
        settings = dict(SettingsService.DEFAULT_SETTINGS)
        db = SessionLocal()
        try:
            items = db.query(ApplicationSetting).all()
            for it in items:
                settings[it.key] = it.value
            return settings
        finally:
            db.close()

    @staticmethod
    def get_family_profile() -> Dict[str, Any]:
        db = SessionLocal()
        try:
            fam = db.query(FamilyProfile).first()
            user_count = db.query(User).count()
            txn_count = db.query(FinancialTransaction).filter_by(is_deleted=False).count()
            return {
                "family_name": fam.family_name if fam else "My Household",
                "user_count": user_count,
                "transaction_count": txn_count
            }
        finally:
            db.close()

    @staticmethod
    def update_family_name(new_name: str) -> bool:
        new_name = new_name.strip()
        if not new_name:
            return False
        db = SessionLocal()
        try:
            fam = db.query(FamilyProfile).first()
            if fam:
                fam.family_name = new_name
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    @staticmethod
    def get_system_diagnostics() -> Dict[str, Any]:
        """Collects runtime environment, storage metrics, and version diagnostics."""
        db_size_mb = round(DB_PATH.stat().st_size / (1024 * 1024), 2) if DB_PATH.exists() else 0.0

        attachment_count = 0
        attachment_size_mb = 0.0
        if ATTACHMENTS_DIR.exists():
            for f in ATTACHMENTS_DIR.rglob("*"):
                if f.is_file():
                    attachment_count += 1
                    attachment_size_mb += f.stat().st_size
        attachment_size_mb = round(attachment_size_mb / (1024 * 1024), 2)

        return {
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "os_version": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "python_version": sys.version.split()[0],
            "pyside6_version": PySide6.__version__,
            "sqlite_version": sqlite3.sqlite_version,
            "sqlalchemy_version": sqlalchemy.__version__,
            "db_path": str(DB_PATH),
            "db_size_mb": db_size_mb,
            "attachment_count": attachment_count,
            "attachment_size_mb": attachment_size_mb,
            "argon2_config": f"Time: {ARGON2_TIME_COST}, Memory: {ARGON2_MEMORY_COST}KB, Parallelism: {ARGON2_PARALLELISM}",
            "offline_status": "100% Offline-First (No external telemetry or internet required)"
        }
