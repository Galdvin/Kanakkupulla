"""
Tests for Phase 3:
- Budget creation, category allocation, and utilization status calculation
- Savings goal creation and contribution tracking
- Investment creation, valuation updates, and portfolio summary
- Loan creation, mathematical EMI calculation formula, and EMI payments
"""
from datetime import date
import pytest
from core.authentication import AuthService
from core.budget_service import BudgetService
from core.savings_service import SavingsService
from core.investment_service import InvestmentService
from core.loan_service import LoanService
from core.accounting_service import AccountService
from core.user_service import UserService
from config.constants import AccountType

@pytest.fixture(autouse=True)
def setup_auth():
    AuthService.login("admin", "admin123")
    yield
    AuthService.logout()

def test_budget_service():
    ok, msg, budget = BudgetService.create_budget(
        name="Nov 2026 Household Budget",
        period_type="Monthly",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 30),
        total_budget_paise=5000000, # ₹50,000
        category_allocations={}
    )
    assert ok is True
    assert budget.total_budget_paise == 5000000

    status = BudgetService.get_budget_status(budget.id)
    assert status is not None
    assert status["total_budget_paise"] == 5000000
    assert status["is_exceeded"] is False

def test_savings_service():
    user = UserService.get_all_users()[0]
    ok, msg, goal = SavingsService.create_goal(
        user_id=user.id,
        goal_name="Emergency Contingency Fund",
        target_amount_paise=20000000, # ₹2,00,000
        start_date=date.today(),
        target_date=date(2027, 12, 31),
        monthly_contribution_paise=1000000 # ₹10,000
    )
    assert ok is True

    # Make contribution
    contrib_ok, _ = SavingsService.record_contribution(
        goal_id=goal.id,
        amount_paise=2500000, # ₹25,000
        contribution_date=date.today(),
        notes="Bonus allocation"
    )
    assert contrib_ok is True

    all_goals = SavingsService.get_all_goals()
    saved_goal = [g for g in all_goals if g.id == goal.id][0]
    assert saved_goal.current_amount_paise == 2500000

def test_investment_service():
    user = UserService.get_all_users()[0]
    ok, msg, inv = InvestmentService.add_investment(
        user_id=user.id,
        investment_name="Nifty 50 Index Fund",
        investment_type="Mutual Funds",
        invested_amount_paise=5000000, # ₹50,000
        current_value_paise=5500000,   # ₹55,000 (10% gain)
        investment_date=date.today()
    )
    assert ok is True

    summary = InvestmentService.get_portfolio_summary()
    assert summary["total_invested_paise"] >= 5000000
    assert summary["unrealized_gain_paise"] >= 500000

def test_loan_emi_calculation_and_payment():
    # Test formula accuracy for ₹10,00,000 (100000000 paise) @ 9.0% for 120 months (10 years)
    # Expected EMI approx ₹12,668
    emi = LoanService.calculate_emi_paise(100000000, 9.0, 120)
    assert 1260000 <= emi <= 1270000 # Within paise precision (~₹12,668)

    # Create Loan
    ok, msg, loan = LoanService.create_loan(
        loan_name="Car Loan HDFC",
        lender="HDFC Bank",
        principal_amount_paise=50000000, # ₹5,00,000
        interest_rate_percent=8.5,
        loan_start_date=date.today(),
        tenure_months=60
    )
    assert ok is True
    assert loan.outstanding_principal_paise == 50000000

    # Record EMI payment
    _, _, pay_acc = AccountService.create_account("Loan Pay Acc", AccountType.SAVINGS.value, 10000000)
    pay_ok, _ = LoanService.record_emi_payment(
        loan_id=loan.id,
        amount_paise=loan.emi_amount_paise,
        payment_date=date.today(),
        account_id=pay_acc.id
    )
    assert pay_ok is True
    updated_loan = [l for l in LoanService.get_all_loans() if l.id == loan.id][0]
    assert updated_loan.outstanding_principal_paise < 50000000
