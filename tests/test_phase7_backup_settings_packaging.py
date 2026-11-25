"""
Phase 7 Automated Verification Test Suite:
Backup & Disaster Recovery Package (.kpk), Settings Service, and Packaging Artifacts.
"""
import pytest
import zipfile
import json
from pathlib import Path
from database.connection import SessionLocal
from database.models import User, FamilyProfile
from core.authentication import AuthService
from core.backup_service import BackupService
from core.settings_service import SettingsService
from config.settings import DB_PATH, ATTACHMENTS_DIR

@pytest.fixture
def test_setup():
    """Authenticate seeded admin user."""
    ok, msg, user = AuthService.login("admin", "admin123")
    assert ok is True
    return user


def test_backup_creation_and_contents(test_setup, tmp_path):
    """Verify full .kpk backup archive creation, database checkpointing, attachments, and manifest."""
    # 1. Create a dummy test attachment
    ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    test_att_file = ATTACHMENTS_DIR / "test_receipt_sample.txt"
    test_att_file.write_text("Receipt #1001 Total ₹4,500.00")

    # 2. Generate Backup
    backup_dest = tmp_path / "backups_out"
    ok, msg, archive_path = BackupService.create_backup(custom_destination_dir=backup_dest, include_attachments=True)

    assert ok is True
    assert archive_path.exists()
    assert archive_path.suffix == ".kpk"
    assert archive_path.stat().st_size > 500

    # 3. Inspect ZIP archive contents
    with zipfile.ZipFile(archive_path, "r") as zipf:
        namelist = zipf.namelist()
        assert "kanakkupulla.db" in namelist
        assert "backup_manifest.json" in namelist
        assert any("test_receipt_sample.txt" in name for name in namelist)

        # Validate manifest JSON structure
        manifest_data = json.loads(zipf.read("backup_manifest.json").decode("utf-8"))
        assert manifest_data["application"] == "Kanakkupulla"
        assert manifest_data["format"] == "kpk_v1"
        assert manifest_data["attachment_files_count"] >= 1

    # Clean up test file
    if test_att_file.exists():
        test_att_file.unlink()


def test_backup_restore_and_integrity(test_setup, tmp_path):
    """Verify restoring from a .kpk archive, integrity check, and safety fallback generation."""
    # 1. Create a known backup
    backup_dest = tmp_path / "restore_test_dir"
    ok_b, _, archive_path = BackupService.create_backup(custom_destination_dir=backup_dest)
    assert ok_b is True

    # 2. Restore from archive
    ok_r, msg_r = BackupService.restore_backup(archive_path)
    assert ok_r is True
    assert "restored successfully" in msg_r.lower()

    # 3. Verify database integrity after restore
    assert BackupService.verify_db_integrity(DB_PATH) is True


def test_settings_service_crud_and_diagnostics(test_setup):
    """Verify settings key-value persistence, family name updates, and environment diagnostics."""
    # 1. Set & Get Setting
    ok_set = SettingsService.set_setting("app_currency_symbol", "₹")
    assert ok_set is True
    assert SettingsService.get_setting("app_currency_symbol") == "₹"

    # 2. Update Family Name
    ok_fam = SettingsService.update_family_name("Sundaram Family Household")
    assert ok_fam is True
    fam_prof = SettingsService.get_family_profile()
    assert fam_prof["family_name"] == "Sundaram Family Household"
    assert fam_prof["user_count"] >= 1

    # 3. System Diagnostics
    diag = SettingsService.get_system_diagnostics()
    assert diag["app_name"] == "Kanakkupulla"
    assert "Windows" in diag["os_version"] or len(diag["os_version"]) > 0
    assert "100% Offline" in diag["offline_status"]
    assert diag["python_version"].startswith("3.")
    assert diag["sqlite_version"] is not None


def test_packaging_spec_and_installer_files_exist():
    """Verify production PyInstaller .spec, Inno Setup .iss, and application icons are present."""
    base_dir = Path.cwd()

    # PyInstaller Spec
    spec_file = base_dir / "Kanakkupulla.spec"
    assert spec_file.exists()
    spec_content = spec_file.read_text(encoding="utf-8")
    assert "main.py" in spec_content
    assert "PySide6" in spec_content
    assert "reportlab" in spec_content
    assert "openpyxl" in spec_content

    # Inno Setup Script
    iss_file = base_dir / "installer" / "kanakkupulla_installer.iss"
    assert iss_file.exists()
    iss_content = iss_file.read_text(encoding="utf-8")
    assert 'MyAppName "Kanakkupulla"' in iss_content
    assert '.kpk' in iss_content

    # App Icons
    ico_file = base_dir / "assets" / "icons" / "app_icon.ico"
    png_file = base_dir / "assets" / "icons" / "app_icon.png"
    assert ico_file.exists()
    assert png_file.exists()
    assert ico_file.stat().st_size > 1000
