"""
Tests for Phase 5:
- Financial Forecasting and Growth/Inflation mathematical modeling
- Database backup creation and restore functionality
"""
import pytest
from analytics.forecasting import ForecastingEngine
from core.backup_service import BackupService
from config.settings import BACKUPS_DIR

def test_financial_forecasting():
    # Monthly Income: ₹60,000 (6000000 paise)
    # Monthly Expenses: ₹35,000 (3500000 paise)
    proj = ForecastingEngine.project_finances(
        monthly_income_paise=6000000,
        monthly_expenses_paise=3500000,
        annual_inflation_pct=6.0,
        expected_income_growth_pct=8.0
    )
    assert proj["current_monthly_savings_paise"] == 2500000
    assert len(proj["projections"]) == 5
    # 1 year horizon should project savings
    one_yr = [p for p in proj["projections"] if p["horizon"] == "1 Year"][0]
    assert one_yr["projected_savings_paise"] > 0
    assert "disclaimer" in proj

def test_database_backup_and_listing():
    ok, msg, path = BackupService.create_backup()
    assert ok is True
    assert path.exists()
    assert path.stat().st_size > 0

    backups = BackupService.list_backups()
    assert len(backups) >= 1
    assert any(b.name == path.name for b in backups)
