"""
Tests for Phase 4 Analytics & Reporting:
- Real DB metric calculations
- Category and user spending distribution aggregations
- Excel (.xlsx) export integrity test
- CSV export integrity test
- PDF export integrity test
"""
from datetime import date
from pathlib import Path
import pytest
from core.authentication import AuthService
from analytics.expense_analysis import AnalyticsService
from reports.reporting_service import ReportingService
from config.settings import DATA_DIR

@pytest.fixture(autouse=True)
def setup_auth():
    AuthService.login("admin", "admin123")
    yield
    AuthService.logout()

def test_dashboard_metrics_aggregation():
    metrics = AnalyticsService.get_dashboard_metrics()
    assert "total_income_paise" in metrics
    assert "total_expense_paise" in metrics
    assert "total_savings_paise" in metrics
    assert "available_bank_balance_paise" in metrics
    assert isinstance(metrics["category_distribution"], list)
    assert isinstance(metrics["user_distribution"], list)

def test_export_excel_csv_pdf():
    test_excel = DATA_DIR / "test_export.xlsx"
    test_csv = DATA_DIR / "test_export.csv"
    test_pdf = DATA_DIR / "test_export.pdf"

    # 1. Test Excel Export
    ok_xlsx = ReportingService.export_transactions_to_excel(test_excel)
    assert ok_xlsx is True
    assert test_excel.exists()
    assert test_excel.stat().st_size > 0

    # 2. Test CSV Export
    ok_csv = ReportingService.export_transactions_to_csv(test_csv)
    assert ok_csv is True
    assert test_csv.exists()
    assert test_csv.stat().st_size > 0

    # 3. Test PDF Export
    ok_pdf = ReportingService.export_summary_to_pdf(test_pdf)
    assert ok_pdf is True
    assert test_pdf.exists()
    assert test_pdf.stat().st_size > 0

    # Cleanup test files
    for p in [test_excel, test_csv, test_pdf]:
        try:
            p.unlink()
        except Exception:
            pass
