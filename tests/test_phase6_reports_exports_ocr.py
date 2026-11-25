"""
Phase 6 Automated Verification Test Suite:
Financial Reporting Aggregation, PDF/Excel Exports, and Smart Receipt OCR Extraction.
"""
import pytest
from pathlib import Path
from datetime import date
from PIL import Image
import openpyxl

from database.connection import SessionLocal
from database.models import (
    User, FamilyProfile, FamilyMember, Account, Category,
    FinancialTransaction
)
from core.authentication import AuthService
from reports.reporting_service import ReportingService
from core.ocr_scanner_service import SmartReceiptScanner
from config.constants import AccountType, TransactionType

@pytest.fixture
def test_setup():
    """Authenticate seeded admin user and add baseline transactions."""
    ok, msg, user = AuthService.login("admin", "admin123")
    assert ok is True

    db = SessionLocal()
    try:
        fam = db.query(FamilyProfile).first()
        admin_member = db.query(FamilyMember).filter_by(user_id=user.id).first()

        spouse = db.query(FamilyMember).filter_by(name="Kavitha").first()
        if not spouse:
            spouse = FamilyMember(family_id=fam.id, name="Kavitha", relation_type="Spouse")
            db.add(spouse)
            db.flush()

        acc = db.query(Account).filter_by(account_type=AccountType.SAVINGS.value).first()
        cat_groceries = db.query(Category).filter_by(name="Food & Dining").first()
        cat_sal = db.query(Category).filter_by(name="Salary & Compensation").first()

        # Add 1 Income and 2 Expenses
        today = date.today()
        t_income = FinancialTransaction(
            title="Monthly Company Salary",
            transaction_type=TransactionType.INCOME.value,
            amount_paise=10000000, # ₹1,00,000
            transaction_date=today,
            account_id=acc.id,
            paid_by_member_id=admin_member.id,
            expense_for_member_id=admin_member.id,
            created_by_user_id=user.id,
            payment_method="Bank Transfer"
        )
        t_exp1 = FinancialTransaction(
            title="Supermarket Grocery",
            transaction_type=TransactionType.EXPENSE.value,
            amount_paise=1500000, # ₹15,000
            transaction_date=today,
            account_id=acc.id,
            paid_by_member_id=admin_member.id,
            expense_for_member_id=spouse.id,
            category_id=cat_groceries.id if cat_groceries else None,
            created_by_user_id=user.id,
            payment_method="UPI"
        )
        t_exp2 = FinancialTransaction(
            title="Dining Out Family",
            transaction_type=TransactionType.EXPENSE.value,
            amount_paise=500000, # ₹5,000
            transaction_date=today,
            account_id=acc.id,
            paid_by_member_id=spouse.id,
            expense_for_member_id=spouse.id,
            category_id=cat_groceries.id if cat_groceries else None,
            created_by_user_id=user.id,
            payment_method="Credit Card"
        )
        db.add_all([t_income, t_exp1, t_exp2])
        db.commit()

        return {
            "family_id": fam.id,
            "user_id": user.id,
            "admin_member_id": admin_member.id,
            "spouse_id": spouse.id,
            "account_id": acc.id
        }
    finally:
        db.close()


def test_financial_reporting_aggregation(test_setup):
    """Verify aggregate metrics, savings rate, category shares, and payer vs beneficiary attribution."""
    today = date.today()
    report = ReportingService.get_financial_report(start_date=today, end_date=today)

    assert report["total_income_paise"] == 10000000 # ₹1,00,000
    assert report["total_expense_paise"] == 2000000  # ₹20,000
    assert report["net_savings_paise"] == 8000000   # ₹80,000
    assert report["savings_rate_pct"] == 80.0       # 80.0%
    assert report["transaction_count"] >= 3

    # Category Breakdown check
    assert len(report["category_breakdown"]) >= 1

    # Member Attribution check (Admin paid ₹15k, Spouse paid ₹5k)
    attribution = report["member_attribution"]
    assert len(attribution) >= 1
    admin_attr = next((m for m in attribution if m["name"] == "Family Head"), None)
    if admin_attr:
        assert admin_attr["paid_paise"] == 1500000


def test_excel_and_pdf_export_generation(test_setup, tmp_path):
    """Verify ReportLab PDF and OpenPyXL Excel export files are created with correct structure."""
    today = date.today()

    # 1. Excel Export (.xlsx)
    excel_path = tmp_path / "test_statement.xlsx"
    ok_excel = ReportingService.export_transactions_to_excel(excel_path, start_date=today, end_date=today)
    assert ok_excel is True
    assert excel_path.exists()
    assert excel_path.stat().st_size > 1000

    wb = openpyxl.load_workbook(excel_path)
    sheet_names = wb.sheetnames
    assert "Executive Summary" in sheet_names
    assert "Transactions Ledger" in sheet_names
    assert "Category Breakdown" in sheet_names
    assert "Family Attribution" in sheet_names
    wb.close()

    # 2. PDF Export (.pdf)
    pdf_path = tmp_path / "test_statement.pdf"
    ok_pdf = ReportingService.export_summary_to_pdf(pdf_path, start_date=today, end_date=today)
    assert ok_pdf is True
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000

    # Verify PDF magic bytes
    with open(pdf_path, "rb") as f:
        header = f.read(4)
        assert header == b"%PDF"

    # 3. CSV Export (.csv)
    csv_path = tmp_path / "test_transactions.csv"
    ok_csv = ReportingService.export_transactions_to_csv(csv_path, start_date=today, end_date=today)
    assert ok_csv is True
    assert csv_path.exists()


def test_smart_receipt_ocr_scanner(tmp_path):
    """Verify receipt scanner image validation and regex heuristic parsing of merchant, date, and amount."""
    # 1. Create a dummy receipt image file
    img_path = tmp_path / "dmart_receipt_nov.png"
    img = Image.new("RGB", (300, 400), color=(255, 255, 255))
    img.save(img_path)

    # 2. Test heuristic parsing with simulated receipt text
    simulated_receipt_text = """
    ========================================
             DMART HYPERMARKET
             AVENUE SUPERMARTS LTD
             GSTIN: 27AABCA1234D1ZM
    Date: 24/11/2026        Time: 14:32
    ----------------------------------------
    1. Aashirvaad Atta 5kg           320.00
    2. Fortune Sunflower Oil 1L      165.50
    3. Tata Salt 1kg                  28.00
    ----------------------------------------
    SUBTOTAL                         513.50
    TAX / CGST/SGST                   24.50
    ----------------------------------------
    GRAND TOTAL:              Rs.    538.00
    ========================================
    """

    parsed = SmartReceiptScanner.parse_bill_image(img_path, raw_text_input=simulated_receipt_text)

    assert "DMart" in parsed["detected_merchant"]
    assert parsed["detected_date"] == date(2026, 11, 24)
    assert parsed["detected_amount_paise"] == 53800 # ₹538.00 in paise
    assert parsed["confidence_score"] >= 0.85
