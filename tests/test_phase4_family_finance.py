"""
Phase 4 Automated Verification Test Suite:
Family Financial Management: Budgets, Savings Goals, Investment Portfolio, and Loans/EMIs.
"""
import pytest
from datetime import date, timedelta
from database.connection import SessionLocal
from database.models import (
    User, FamilyProfile, FamilyMember, Account, Category,
    FinancialTransaction, Budget, SavingsGoal, Investment, Loan
)
from core.authentication import AuthService
from core.budget_service import BudgetService, BudgetAlertLevel
from core.savings_service import SavingsService
from core.investment_service import InvestmentService
from core.loan_service import LoanService
from config.constants import AccountType, TransactionType, GoalPriority, LoanStatus

@pytest.fixture
def test_setup():
    """Authenticate seeded admin user and add secondary family members."""
    ok, msg, user = AuthService.login("admin", "admin123")
    assert ok is True

    db = SessionLocal()
    try:
        fam = db.query(FamilyProfile).first()
        admin_member = db.query(FamilyMember).filter_by(user_id=user.id).first()

        # Add spouse and child members if not present
        spouse = db.query(FamilyMember).filter_by(name="Kavitha").first()
        if not spouse:
            spouse = FamilyMember(family_id=fam.id, name="Kavitha", relation_type="Spouse")
            db.add(spouse)

        child = db.query(FamilyMember).filter_by(name="Rohan").first()
        if not child:
            child = FamilyMember(family_id=fam.id, name="Rohan", relation_type="Child")
            db.add(child)

        acc = db.query(Account).filter_by(account_type=AccountType.SAVINGS.value).first()
        # Set generous balance
        acc.current_balance_paise = 50000000 # ₹5,00,000

        cat_groceries = db.query(Category).filter_by(name="Food & Dining").first()
        if not cat_groceries:
            cat_groceries = Category(name="Food & Dining", category_type="Expense")
            db.add(cat_groceries)

        cat_edu = db.query(Category).filter_by(name="Education").first()
        if not cat_edu:
            cat_edu = Category(name="Education", category_type="Expense")
            db.add(cat_edu)

        cat_health = db.query(Category).filter_by(name="Healthcare").first()
        if not cat_health:
            cat_health = Category(name="Healthcare", category_type="Expense")
            db.add(cat_health)

        db.commit()

        return {
            "family_id": fam.id,
            "user_id": user.id,
            "father_id": admin_member.id,
            "mother_id": spouse.id,
            "child_id": child.id,
            "account_id": acc.id,
            "cat_groceries_id": cat_groceries.id,
            "cat_edu_id": cat_edu.id,
            "cat_health_id": cat_health.id
        }
    finally:
        db.close()


def test_budget_service_shared_and_individual(test_setup):
    """Verify shared family budgets vs individual member budgets, spending tracking, and alert tiers."""
    data = test_setup
    today = date.today()
    start_d = date(today.year, today.month, 1)
    end_d = date(today.year, today.month, 28)

    # 1. Create a shared family budget: ₹30,000 (3,000,000 paise)
    ok, msg, budget = BudgetService.create_budget(
        name="March Household Budget",
        period_type="Monthly",
        start_date=start_d,
        end_date=end_d,
        total_budget_paise=3000000,
        category_allocations={
            data["cat_groceries_id"]: 1500000, # ₹15,000
            data["cat_health_id"]: 500000     # ₹5,000
        },
        family_member_id=None # Shared family budget
    )
    assert ok is True
    assert budget is not None

    # Status before spending: 0% utilization, alert NORMAL
    st = BudgetService.get_budget_status(budget.id)
    assert st["total_spent_paise"] == 0
    assert st["remaining_paise"] == 3000000
    assert st["alert_level"] == BudgetAlertLevel.NORMAL

    # 2. Add an expense of ₹24,000 (80% utilization -> CAUTION alert)
    db = SessionLocal()
    try:
        txn1 = FinancialTransaction(
            title="Supermarket Weekly Grocery",
            account_id=data["account_id"],
            created_by_user_id=data["user_id"],
            paid_by_member_id=data["father_id"],
            expense_for_member_id=data["mother_id"],
            category_id=data["cat_groceries_id"],
            transaction_date=start_d,
            transaction_type=TransactionType.EXPENSE.value,
            amount_paise=2400000, # ₹24,000
            expense_kind="Daily",
            payment_method="Bank Transfer"
        )
        db.add(txn1)
        db.commit()
    finally:
        db.close()

    st_after1 = BudgetService.get_budget_status(budget.id)
    assert st_after1["total_spent_paise"] == 2400000
    assert st_after1["remaining_paise"] == 600000
    assert st_after1["utilization_pct"] == 80.0
    assert st_after1["alert_level"] == BudgetAlertLevel.CAUTION

    # 3. Add an expense of ₹4,000 (Total ₹28,000 = 93.3% -> WARNING alert)
    db = SessionLocal()
    try:
        txn2 = FinancialTransaction(
            title="Doctor Consultation and Pharmacy",
            account_id=data["account_id"],
            created_by_user_id=data["user_id"],
            paid_by_member_id=data["father_id"],
            expense_for_member_id=data["father_id"],
            category_id=data["cat_health_id"],
            transaction_date=start_d,
            transaction_type=TransactionType.EXPENSE.value,
            amount_paise=400000, # ₹4,000
            expense_kind="Daily",
            payment_method="UPI"
        )
        db.add(txn2)
        db.commit()
    finally:
        db.close()

    st_after2 = BudgetService.get_budget_status(budget.id)
    assert st_after2["total_spent_paise"] == 2800000
    assert st_after2["utilization_pct"] == 93.3
    assert st_after2["alert_level"] == BudgetAlertLevel.WARNING

    # 4. Create an individual budget specifically for Rohan (Child Education): ₹10,000
    ok2, _, child_budget = BudgetService.create_budget(
        name="Rohan School Term Budget",
        period_type="Monthly",
        start_date=start_d,
        end_date=end_d,
        total_budget_paise=1000000,
        category_allocations={data["cat_edu_id"]: 1000000},
        family_member_id=data["child_id"]
    )
    assert ok2 is True

    # Rohan's budget should only track expenses where Rohan is beneficiary
    st_child = BudgetService.get_budget_status(child_budget.id)
    assert st_child["total_spent_paise"] == 0 # Previous ₹28,000 was for father/mother!

    # Record expense for Rohan ₹11,000 (110% -> EXCEEDED alert)
    db = SessionLocal()
    try:
        txn3 = FinancialTransaction(
            title="School Annual Term Fees",
            account_id=data["account_id"],
            created_by_user_id=data["user_id"],
            paid_by_member_id=data["father_id"],
            expense_for_member_id=data["child_id"],
            category_id=data["cat_edu_id"],
            transaction_date=start_d,
            transaction_type=TransactionType.EXPENSE.value,
            amount_paise=1100000, # ₹11,000
            expense_kind="Occasional",
            payment_method="Net Banking"
        )
        db.add(txn3)
        db.commit()
    finally:
        db.close()

    st_child_after = BudgetService.get_budget_status(child_budget.id)
    assert st_child_after["total_spent_paise"] == 1100000
    assert st_child_after["is_exceeded"] is True
    assert st_child_after["alert_level"] == BudgetAlertLevel.EXCEEDED


def test_savings_service_goals_and_contributions(test_setup):
    """Verify savings goals creation, periodic deposits, account balance reduction, and goal completion."""
    data = test_setup
    today = date.today()

    # Create Goal: ₹1,00,000 (10,000,000 paise)
    ok, msg, goal = SavingsService.create_goal(
        family_member_id=data["father_id"],
        goal_name="Emergency Reserve Fund",
        target_amount_paise=10000000,
        start_date=today,
        target_date=today + timedelta(days=180),
        monthly_contribution_paise=2000000,
        priority=GoalPriority.CRITICAL.value,
        notes="6-month living expenses backup"
    )
    assert ok is True
    assert goal.current_amount_paise == 0
    assert goal.is_completed is False

    # Check account initial balance: ₹5,00,000 (50,000,000 paise)
    db = SessionLocal()
    initial_bal = db.query(Account).filter_by(id=data["account_id"]).first().current_balance_paise
    db.close()
    assert initial_bal == 50000000

    # 1. Record deposit of ₹40,000 from account
    ok_dep1, msg_dep1 = SavingsService.record_contribution(
        goal_id=goal.id,
        amount_paise=4000000,
        contribution_date=today,
        account_id=data["account_id"],
        notes="Initial deposit"
    )
    assert ok_dep1 is True

    # Verify goal and account balances
    db = SessionLocal()
    updated_goal = db.query(SavingsGoal).filter_by(id=goal.id).first()
    updated_acc = db.query(Account).filter_by(id=data["account_id"]).first()
    assert updated_goal.current_amount_paise == 4000000
    assert updated_goal.is_completed is False
    assert updated_acc.current_balance_paise == 46000000 # Deducted 40,000
    db.close()

    # 2. Record deposit of ₹60,000 (completes the target)
    ok_dep2, _ = SavingsService.record_contribution(
        goal_id=goal.id,
        amount_paise=6000000,
        contribution_date=today,
        account_id=data["account_id"],
        notes="Final milestone deposit"
    )
    assert ok_dep2 is True

    db = SessionLocal()
    completed_goal = db.query(SavingsGoal).filter_by(id=goal.id).first()
    assert completed_goal.current_amount_paise == 10000000
    assert completed_goal.is_completed is True
    db.close()

    # Summary verification
    summary = SavingsService.get_savings_summary(data["father_id"])
    assert summary["total_target_paise"] == 10000000
    assert summary["total_saved_paise"] == 10000000
    assert summary["progress_pct"] == 100.0
    assert summary["completed_goals_count"] == 1


def test_investment_service_portfolio_and_valuations(test_setup):
    """Verify adding investments, market valuation adjustments, gain/loss calculations, and asset allocation."""
    data = test_setup
    today = date.today()

    # 1. Add Mutual Fund holding: Invested ₹50,000, initial value ₹50,000
    ok1, _, mf = InvestmentService.add_investment(
        family_member_id=data["father_id"],
        investment_name="Parag Parikh Flexi Cap Fund",
        investment_type="Mutual Funds",
        invested_amount_paise=5000000,
        current_value_paise=5000000,
        investment_date=today - timedelta(days=90),
        institution="Groww"
    )
    assert ok1 is True

    # 2. Add Sovereign Gold Bond: Invested ₹30,000
    ok2, _, gold = InvestmentService.add_investment(
        family_member_id=data["mother_id"],
        investment_name="SGB 2024 Series",
        investment_type="Gold & Precious Metals",
        invested_amount_paise=3000000,
        current_value_paise=3000000,
        investment_date=today - timedelta(days=60),
        institution="Zerodha"
    )
    assert ok2 is True

    # 3. Update Mutual Fund valuation to ₹65,000 (gain of ₹15,000)
    ok_val, msg_val = InvestmentService.update_valuation(mf.id, 6500000)
    assert ok_val is True

    # 4. Check aggregate portfolio summary
    summary = InvestmentService.get_portfolio_summary()
    assert summary["total_invested_paise"] == 8000000 # ₹80,000
    assert summary["total_current_paise"] == 9500000  # ₹95,000
    assert summary["unrealized_gain_paise"] == 1500000 # +₹15,000
    assert summary["returns_pct"] == 18.75 # 15000 / 80000 * 100 = 18.75%
    assert summary["count"] == 2
    assert summary["asset_allocation"]["Mutual Funds"] == 6500000
    assert summary["asset_allocation"]["Gold & Precious Metals"] == 3000000


def test_loan_service_amortization_and_payments(test_setup):
    """Verify EMI amortization formula, loan creation, and payment splitting into principal reduction and interest."""
    data = test_setup
    today = date.today()

    # 1. Test mathematical accuracy of standard EMI formula:
    # Principal: ₹10,00,000 (100,000,000 paise), Rate: 12.0% p.a., Tenure: 12 months
    # EMI = [P x r x (1+r)^n] / [(1+r)^n - 1]
    # For P=10,00,000, r=0.01, n=12:
    # (1+r)^12 = 1.01^12 = 1.12682503
    # EMI = [1000000 * 0.01 * 1.12682503] / [0.12682503] = 11268.2503 / 0.12682503 = 88848.788...
    # In paise: ~8884879 paise (₹88,848.79)
    emi_calc = LoanService.calculate_emi_paise(100000000, 12.0, 12)
    assert abs(emi_calc - 8884879) < 100 # Within ₹1 accuracy of mathematical formula

    # 2. Create Loan in DB
    ok, _, loan = LoanService.create_loan(
        loan_name="Car Loan HDFC",
        lender="HDFC Bank",
        principal_amount_paise=100000000,
        interest_rate_percent=12.0,
        loan_start_date=today,
        tenure_months=12,
        family_member_id=data["father_id"],
        emi_due_day=5
    )
    assert ok is True
    assert loan.outstanding_principal_paise == 100000000
    assert loan.status == LoanStatus.ACTIVE.value

    # 3. Record first EMI payment: ₹88,849
    # Monthly interest for month 1 = 10,00,000 * (0.12 / 12) = ₹10,000 (1,000,000 paise)
    # Principal component = 88,849 - 10,000 = ₹78,849 (7,884,879 paise)
    # New outstanding balance = 10,00,000 - 78,849 = ₹9,21,151
    ok_pay, msg_pay = LoanService.record_emi_payment(
        loan_id=loan.id,
        amount_paise=loan.emi_amount_paise,
        payment_date=today,
        account_id=data["account_id"],
        payment_method="Auto Debit / ECS",
        reference="ACH-HDFC-001"
    )
    assert ok_pay is True

    db = SessionLocal()
    updated_loan = db.query(Loan).filter_by(id=loan.id).first()
    assert updated_loan.payments[0].interest_component_paise == 1000000 # Exactly ₹10,000 interest
    assert updated_loan.payments[0].principal_component_paise == loan.emi_amount_paise - 1000000
    assert updated_loan.outstanding_principal_paise == 100000000 - updated_loan.payments[0].principal_component_paise
    db.close()

    # 4. Check Loan Summary
    summary = LoanService.get_loan_summary()
    assert summary["total_principal_paise"] == 100000000
    assert summary["active_loans_count"] == 1
    assert summary["monthly_emi_paise"] == loan.emi_amount_paise
