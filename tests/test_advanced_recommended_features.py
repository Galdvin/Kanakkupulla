"""
Automated Tests for the 5 High-Impact Recommended Features:
1. Daily Spending Heatmap Service
2. Net Worth Calculation Engine
3. Subscription and Recurring Payment Tracker
4. Year-over-Year (YoY) Growth Engine
5. Smart Receipt Scanner OCR parsing
"""
from datetime import date
from pathlib import Path
import pytest
from analytics.net_worth_service import NetWorthService
from analytics.heatmap_service import HeatmapService
from analytics.yoy_service import YearOverYearService
from core.subscription_service import SubscriptionService
from core.ocr_scanner_service import SmartReceiptScanner
from core.authentication import AuthService
from core.user_service import UserService
from core.accounting_service import AccountService
from config.constants import RecurringFrequency

@pytest.fixture(autouse=True)
def setup_auth():
    AuthService.login("admin", "admin123")
    yield
    AuthService.logout()

def test_net_worth_calculation():
    nw = NetWorthService.calculate_current_net_worth()
    assert "total_assets_paise" in nw
    assert "total_liabilities_paise" in nw
    assert "net_worth_paise" in nw
    assert nw["net_worth_paise"] == (nw["total_assets_paise"] - nw["total_liabilities_paise"])

def test_daily_spending_heatmap():
    today = date.today()
    hm = HeatmapService.get_spending_heatmap(today.year, today.month)
    assert hm["year"] == today.year
    assert hm["month"] == today.month
    assert len(hm["days"]) >= 28
    for d in hm["days"]:
        assert 0 <= d["intensity_level"] <= 4

def test_subscriptions_service():
    user = UserService.get_all_users()[0]
    acc = AccountService.get_all_accounts()[0]

    ok, msg = SubscriptionService.add_subscription(
        title="Netflix 4K Ultra",
        amount_paise=64900, # ₹649.00 / month
        frequency=RecurringFrequency.MONTHLY.value,
        start_date=date.today(),
        next_due_date=date.today(),
        account_id=acc.id,
        paid_by_id=user.id
    )
    assert ok is True

    subs = SubscriptionService.get_all_subscriptions()
    assert len(subs) >= 1
    netflix = [s for s in subs if s["title"] == "Netflix 4K Ultra"][0]
    assert netflix["annual_paise"] == (64900 * 12)

def test_year_over_year_comparison():
    yoy = YearOverYearService.compare_years(2025, 2026)
    assert yoy["base_year"] == 2025
    assert yoy["target_year"] == 2026
    assert "income_growth_pct" in yoy
    assert "expense_growth_pct" in yoy

def test_smart_receipt_scanner():
    dummy_img = Path("test_grocery_bill.jpg")
    parsed = SmartReceiptScanner.parse_bill_image(dummy_img)
    assert parsed["detected_category"] == "Groceries"
    assert parsed["detected_amount_paise"] > 0
    assert "Reliance" in parsed["detected_merchant"] or "DMart" in parsed["detected_merchant"]
