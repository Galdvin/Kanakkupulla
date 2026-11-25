"""
Phase 8 End-to-End Smoke Test & UI Verification Suite:
Validates the entire financial platform lifecycle:
1. End-to-End Financial User Journey:
   - User authentication & Family Profile
   - Account creation & Double-entry transfer (Rule 1)
   - Credit card swipe & bill settlement (Rule 2)
   - Expense entry with receipt attachment
   - Budget allocation & threshold alert
   - Savings goal contribution
   - Investment portfolio valuation
   - Loan EMI amortization & repayment (Rule 4)
   - Recurring rules execution engine
   - Financial calendar aggregation
   - Cash runway & 12-month forecasting
   - Multi-tab Excel & ReportLab PDF generation
   - Full package backup (.kpk) & verified restore
   - Global double-entry balance check: sum(Debits) == sum(Credits)
2. Headless UI Smoke Test:
   - Verifies MainWindow and all 19 stacked pages initialize without UI freezes or runtime errors.
"""
import pytest
from pathlib import Path
from datetime import date, timedelta
from database.connection import SessionLocal
from database.models import (
    User, FamilyProfile, FamilyMember, Account, Category,
    FinancialTransaction, Budget, SavingsGoal, Investment, Loan, LedgerEntry
)
from core.authentication import AuthService
from core.accounting_service import AccountService, AccountingService
from core.accounting_service_engine import AccountingEngineService
from core.expense_service import ExpenseService
from core.income_service import IncomeService
from core.budget_service import BudgetService
from core.savings_service import SavingsService
from core.investment_service import InvestmentService
from core.loan_service import LoanService
from core.recurring_service import RecurringService
from core.calendar_service import CalendarService
from analytics.forecasting import ForecastingEngine
from reports.reporting_service import ReportingService
from core.backup_service import BackupService
from config.constants import AccountType, TransactionType
from ui.main_window import MainWindow

def test_full_financial_platform_lifecycle_e2e(tmp_path):
    """Executes a complete financial lifecycle across all modules and verifies double-entry integrity."""
    # 1. Authenticate Admin User
    ok_auth, msg, user = AuthService.login("admin", "admin123")
    assert ok_auth is True
    assert user is not None

    db = SessionLocal()
    try:
        fam = db.query(FamilyProfile).first()
        admin_member = db.query(FamilyMember).filter_by(user_id=user.id).first()

        # Add Spouse and Child members
        spouse = db.query(FamilyMember).filter_by(name="Kavitha").first()
        if not spouse:
            spouse = FamilyMember(family_id=fam.id, name="Kavitha", relation_type="Spouse")
            db.add(spouse)

        child = db.query(FamilyMember).filter_by(name="Rohan").first()
        if not child:
            child = FamilyMember(family_id=fam.id, name="Rohan", relation_type="Child")
            db.add(child)
        db.commit()

        spouse_id = spouse.id
        child_id = child.id
        admin_member_id = admin_member.id
    finally:
        db.close()

    # 2. Setup Accounts (Savings Bank, Cash, Credit Card)
    ok_acc1, _, bank_acc = AccountService.create_account(
        name="HDFC Salary Account",
        account_type=AccountType.SAVINGS.value,
        opening_balance_paise=50000000 # ₹5,00,000
    )
    ok_acc2, _, cash_acc = AccountService.create_account(
        name="Household Cash Drawer",
        account_type=AccountType.CASH.value,
        opening_balance_paise=2000000 # ₹20,000
    )
    ok_acc3, _, cc_acc = AccountService.create_account(
        name="ICICI Coral Credit Card",
        account_type=AccountType.CREDIT_CARD.value,
        credit_limit_paise=15000000 # ₹1,50,000
    )
    assert ok_acc1 and ok_acc2 and ok_acc3

    today = date.today()

    # 3. Rule 1: Internal Account Transfer (Bank -> Cash ₹10,000)
    ok_tr, msg_tr = AccountingService.record_transfer(
        from_account_id=bank_acc.id,
        to_account_id=cash_acc.id,
        amount_paise=1000000,
        transfer_date=today,
        notes="ATM Cash Withdrawal for home"
    )
    assert ok_tr is True

    # 4. Record Daily Expense (Groceries ₹4,500)
    db = SessionLocal()
    cat_food = db.query(Category).filter_by(name="Food & Dining").first()
    db.close()

    ok_exp, _, exp_txn = ExpenseService.record_expense(
        title="Weekly Supermarket Restock",
        amount_paise=450000,
        transaction_date=today,
        account_id=bank_acc.id,
        category_id=cat_food.id if cat_food else None,
        paid_by_member_id=admin_member_id,
        expense_for_member_id=spouse_id,
        payment_method="UPI",
        expense_kind="Daily"
    )
    assert ok_exp is True

    # 5. Rule 2: Credit Card Purchase (Flight tickets ₹12,000) & Card Bill Settlement
    ok_cc_buy, _, _ = ExpenseService.record_expense(
        title="Flight Tickets to Chennai",
        amount_paise=1200000,
        transaction_date=today,
        account_id=cc_acc.id,
        category_id=cat_food.id if cat_food else None,
        paid_by_member_id=admin_member_id,
        expense_for_member_id=admin_member_id,
        payment_method="Credit Card",
        expense_kind="Occasional"
    )
    assert ok_cc_buy is True

    ok_cc_pay, _ = AccountingService.pay_credit_card_bill(
        from_account_id=bank_acc.id,
        card_account_id=cc_acc.id,
        amount_paise=1200000,
        payment_date=today,
        reference="CC-SETTLE-001"
    )
    assert ok_cc_pay is True

    # 6. Budget Creation & Status Check
    ok_b, _, budget = BudgetService.create_budget(
        name="Household Monthly Budget",
        period_type="Monthly",
        start_date=date(today.year, today.month, 1),
        end_date=date(today.year, today.month, 28),
        total_budget_paise=5000000, # ₹50,000 cap
        category_allocations={cat_food.id: 2500000} if cat_food else {}
    )
    assert ok_b is True
    st_b = BudgetService.get_budget_status(budget.id)
    assert st_b["total_spent_paise"] > 0
    assert st_b["alert_level"] is not None

    # 7. Savings Goal & Contribution
    ok_g, _, goal = SavingsService.create_goal(
        family_member_id=admin_member_id,
        goal_name="Emergency Reserve Fund",
        target_amount_paise=10000000, # ₹1,00,000
        start_date=today,
        target_date=today + timedelta(days=180)
    )
    assert ok_g is True
    ok_dep, _ = SavingsService.record_contribution(
        goal_id=goal.id,
        amount_paise=2500000, # ₹25,000
        contribution_date=today,
        account_id=bank_acc.id
    )
    assert ok_dep is True

    # 8. Investment Holding & Valuation
    ok_inv, _, inv = InvestmentService.add_investment(
        family_member_id=admin_member_id,
        investment_name="Nippon India Small Cap",
        investment_type="Mutual Funds",
        invested_amount_paise=5000000,
        current_value_paise=5000000,
        investment_date=today
    )
    assert ok_inv is True
    ok_val, _ = InvestmentService.update_valuation(inv.id, 5500000) # Grew to ₹55,000
    assert ok_val is True
    port_sum = InvestmentService.get_portfolio_summary()
    assert port_sum["unrealized_gain_paise"] >= 500000

    # 9. Loan Creation & EMI Payment (Rule 4)
    ok_l, _, loan = LoanService.create_loan(
        loan_name="Car Financing SBI",
        lender="State Bank of India",
        principal_amount_paise=60000000, # ₹6,00,000
        interest_rate_percent=9.0,
        loan_start_date=today,
        tenure_months=36,
        family_member_id=admin_member_id,
        emi_due_day=5
    )
    assert ok_l is True
    ok_emi, _ = LoanService.record_emi_payment(
        loan_id=loan.id,
        amount_paise=loan.emi_amount_paise,
        payment_date=today,
        account_id=bank_acc.id
    )
    assert ok_emi is True

    # 10. Recurring Rule & Execution
    ok_r, _, rule = RecurringService.create_rule(
        title="High-Speed Fiber Broadband",
        transaction_type=TransactionType.EXPENSE.value,
        amount_paise=150000, # ₹1,500
        frequency="Monthly",
        start_date=today,
        account_id=bank_acc.id,
        paid_by_member_id=admin_member_id
    )
    assert ok_r is True
    processed_count, _ = RecurringService.process_due_rules(up_to_date=today)
    assert processed_count >= 1

    # 11. Financial Calendar Aggregation
    cal = CalendarService.get_month_calendar_data(today.year, today.month)
    assert cal["total_actual_expense_paise"] > 0
    assert cal["total_scheduled_expense_paise"] > 0

    # 12. Cash Runway & Forecasting
    runway = ForecastingEngine.get_cash_runway()
    assert runway["runway_months"] > 0
    forecast_12m = ForecastingEngine.project_12_month_cashflow()
    assert len(forecast_12m["monthly_projections"]) == 12

    # 13. Reports: Excel & PDF Exports
    excel_file = tmp_path / "Final_E2E_Report.xlsx"
    pdf_file = tmp_path / "Final_E2E_Statement.pdf"
    assert ReportingService.export_transactions_to_excel(excel_file) is True
    assert ReportingService.export_summary_to_pdf(pdf_file) is True
    assert excel_file.stat().st_size > 1000
    assert pdf_file.stat().st_size > 1000

    # 14. Package Backup (.kpk) & Integrity Verification
    ok_bup, _, bup_path = BackupService.create_backup(custom_destination_dir=tmp_path)
    assert ok_bup is True
    assert bup_path.suffix == ".kpk"
    ok_res, _ = BackupService.restore_backup(bup_path)
    assert ok_res is True

    # 15. Global Balanced Double-Entry Ledger Invariant Check
    # Total debits across the entire general ledger must strictly equal total credits!
    db = SessionLocal()
    all_ledgers = db.query(LedgerEntry).all()
    total_debits = sum(e.amount_paise for e in all_ledgers if e.entry_type.upper() == "DEBIT")
    total_credits = sum(e.amount_paise for e in all_ledgers if e.entry_type.upper() == "CREDIT")
    db.close()

    assert total_debits > 0
    assert total_credits > 0
    assert total_debits == total_credits, f"General ledger imbalance detected: Debits={total_debits}, Credits={total_credits}"


def test_main_window_headless_navigation(qtbot):
    """Verifies MainWindow and all 19 stacked pages initialize and switch seamlessly without runtime errors."""
    ok_auth, _, user = AuthService.login("admin", "admin123")
    assert ok_auth is True

    window = MainWindow(user=user)
    qtbot.addWidget(window)

    # Test all 19 stacked pages (0 through 18)
    expected_pages_count = 19
    assert window.stack.count() >= expected_pages_count

    for page_idx in range(expected_pages_count):
        window.switch_page(page_idx)
        assert window.stack.currentIndex() == page_idx
        # Check active widget exists
        current_widget = window.stack.currentWidget()
        assert current_widget is not None

    # Test theme toggle
    window.toggle_theme()
    assert window.is_dark_mode is False
    window.toggle_theme()
    assert window.is_dark_mode is True

