"""
Phase 5 Automated Verification Test Suite:
Recurring Rules Engine, Financial Calendar Aggregation, and Financial Planning/Cash Runway.
"""
import pytest
from datetime import date, timedelta
from database.connection import SessionLocal
from database.models import (
    User, FamilyProfile, FamilyMember, Account, Category,
    FinancialTransaction, RecurringRule, Loan, LedgerEntry
)
from core.authentication import AuthService
from core.recurring_service import RecurringService
from core.calendar_service import CalendarService
from core.loan_service import LoanService
from analytics.forecasting import ForecastingEngine
from config.constants import AccountType, TransactionType, LoanStatus

@pytest.fixture
def test_setup():
    """Authenticate seeded admin user and verify family/account baseline."""
    ok, msg, user = AuthService.login("admin", "admin123")
    assert ok is True

    db = SessionLocal()
    try:
        fam = db.query(FamilyProfile).first()
        admin_member = db.query(FamilyMember).filter_by(user_id=user.id).first()

        acc = db.query(Account).filter_by(account_type=AccountType.SAVINGS.value).first()
        acc.current_balance_paise = 50000000 # ₹5,00,000

        cat_rent = db.query(Category).filter_by(name="Housing & Utilities").first()
        if not cat_rent:
            cat_rent = Category(name="Housing & Utilities", category_type="Expense")
            db.add(cat_rent)

        cat_sal = db.query(Category).filter_by(name="Salary & Compensation").first()
        if not cat_sal:
            cat_sal = Category(name="Salary & Compensation", category_type="Income")
            db.add(cat_sal)

        db.commit()

        return {
            "family_id": fam.id,
            "user_id": user.id,
            "member_id": admin_member.id,
            "account_id": acc.id,
            "cat_rent_id": cat_rent.id,
            "cat_sal_id": cat_sal.id
        }
    finally:
        db.close()


def test_recurring_rule_creation_and_processing(test_setup):
    """Verify creating a recurring rule, executing it, balance deduction, double-entry ledger, and next date advancement."""
    data = test_setup
    today = date.today()

    # 1. Create a monthly recurring expense: ₹20,000 (2,000,000 paise)
    ok, msg, rule = RecurringService.create_rule(
        title="Apartment Rent Auto-Debit",
        transaction_type=TransactionType.EXPENSE.value,
        amount_paise=2000000,
        frequency="Monthly",
        start_date=today,
        account_id=data["account_id"],
        paid_by_member_id=data["member_id"],
        category_id=data["cat_rent_id"]
    )
    assert ok is True
    assert rule is not None
    assert rule.next_due_date == today
    assert rule.is_active is True

    # Initial balance check
    db = SessionLocal()
    bal_before = db.query(Account).filter_by(id=data["account_id"]).first().current_balance_paise
    db.close()

    # 2. Execute due rules up to today
    count, created = RecurringService.process_due_rules(up_to_date=today)
    assert count == 1
    assert created[0]["title"] == "Apartment Rent Auto-Debit"
    assert created[0]["amount_paise"] == 2000000

    # 3. Verify Account balance reduced
    db = SessionLocal()
    bal_after = db.query(Account).filter_by(id=data["account_id"]).first().current_balance_paise
    assert bal_after == bal_before - 2000000

    # 4. Verify Transaction and Balanced Ledger Entries
    txn_id = created[0]["transaction_id"]
    txn = db.query(FinancialTransaction).filter_by(id=txn_id).first()
    assert txn is not None
    assert txn.is_recurring is True

    ledgers = db.query(LedgerEntry).filter_by(transaction_id=txn_id).all()
    assert len(ledgers) >= 2
    sum_debit = sum(e.amount_paise for e in ledgers if e.entry_type.upper() == "DEBIT")
    sum_credit = sum(e.amount_paise for e in ledgers if e.entry_type.upper() == "CREDIT")
    assert sum_debit == sum_credit == 2000000 # Perfect double-entry balance

    # 5. Verify rule next_due_date advanced by 1 month
    updated_rule = db.query(RecurringRule).filter_by(id=rule.id).first()
    assert updated_rule.next_due_date > today
    db.close()

    # 6. Re-running immediately should process 0 transactions
    count_again, _ = RecurringService.process_due_rules(up_to_date=today)
    assert count_again == 0


def test_financial_calendar_aggregation(test_setup):
    """Verify daily transaction mapping, loan EMI events, and month summary calculations in calendar."""
    data = test_setup
    today = date.today()

    # Post an actual transaction on 5th of current month
    d5 = date(today.year, today.month, 5)
    db = SessionLocal()
    try:
        t1 = FinancialTransaction(
            title="Weekly Fresh Groceries",
            transaction_type=TransactionType.EXPENSE.value,
            expense_kind="Daily",
            amount_paise=150000, # ₹1,500
            transaction_date=d5,
            account_id=data["account_id"],
            paid_by_member_id=data["member_id"],
            expense_for_member_id=data["member_id"],
            created_by_user_id=data["user_id"],
            payment_method="UPI"
        )
        db.add(t1)
        db.commit()
    finally:
        db.close()

    # Add an active loan with EMI due on the 10th
    ok_l, _, loan = LoanService.create_loan(
        loan_name="Vehicle Loan Axis",
        lender="Axis Bank",
        principal_amount_paise=50000000, # ₹5,00,000
        interest_rate_percent=9.5,
        loan_start_date=today,
        tenure_months=36,
        family_member_id=data["member_id"],
        emi_due_day=10
    )
    assert ok_l is True

    # Query calendar service for current month
    cal_data = CalendarService.get_month_calendar_data(today.year, today.month)
    assert cal_data["year"] == today.year
    assert cal_data["month"] == today.month
    assert cal_data["num_days"] >= 28

    # Verify Day 5 has actual expense
    day5 = cal_data["daily_data"][5]
    assert day5["actual_expense_paise"] == 150000
    assert len(day5["transactions"]) >= 1

    # Verify Day 10 has loan EMI scheduled
    day10 = cal_data["daily_data"][10]
    assert day10["scheduled_expense_paise"] == loan.emi_amount_paise
    assert any(ev["kind"] == "Loan EMI" for ev in day10["scheduled_events"])

    # Verify monthly totals
    assert cal_data["total_actual_expense_paise"] >= 150000
    assert cal_data["total_scheduled_expense_paise"] >= loan.emi_amount_paise


def test_cash_runway_and_12_month_forecasting(test_setup):
    """Verify cash runway buffer calculation, health status, and 12-month forward simulation."""
    data = test_setup

    # 1. Runway Calculation
    runway = ForecastingEngine.get_cash_runway()
    assert runway["total_liquid_paise"] > 0
    assert runway["total_monthly_burn_paise"] > 0
    assert runway["runway_months"] > 0
    assert runway["health_status"] is not None

    # 2. 12-Month Simulation
    sim = ForecastingEngine.project_12_month_cashflow(
        annual_inflation_pct=6.0,
        expected_income_growth_pct=8.0,
        custom_monthly_income_paise=10000000 # Assume ₹1,00,000 monthly income
    )
    assert sim["starting_cash_paise"] == runway["total_liquid_paise"]
    assert len(sim["monthly_projections"]) == 12

    # Check that projections are compounding forward
    p1 = sim["monthly_projections"][0]
    p12 = sim["monthly_projections"][11]

    assert p12["projected_income_paise"] > p1["projected_income_paise"] # Income growth
    assert p12["variable_expenses_paise"] > p1["variable_expenses_paise"] # Inflation increase
    assert sim["final_projected_cash_paise"] > 0
