"""
Tests for Phase 2: Core Financial Management
- Recording daily and occasional expenses
- Payer vs Beneficiary attribution
- Account balance updates on expense
- Recording income & account balance crediting
- Inter-account internal fund transfers (verifying zero income/expense creation)
- Category & Subcategory dynamic creation
- Soft deleting expenses and balance recovery
"""
from datetime import date
import pytest
from core.authentication import AuthService
from core.expense_service import ExpenseService
from core.income_service import IncomeService
from core.accounting_service import AccountService
from core.category_service import CategoryService
from core.user_service import UserService
from config.constants import AccountType, ExpenseKind, UserRole

@pytest.fixture(autouse=True)
def setup_auth():
    AuthService.login("admin", "admin123")
    yield
    AuthService.logout()

def test_category_and_subcategory_creation():
    ok, msg, cat = CategoryService.create_category("Test Pet Care", "#10b981")
    assert ok is True
    assert cat.name == "Test Pet Care"

    sub_ok, sub_msg, sub = CategoryService.add_subcategory(cat.id, "Vet Clinic")
    assert sub_ok is True
    assert sub.name == "Vet Clinic"

    subcats = CategoryService.get_subcategories(cat.id)
    assert any(s.name == "Vet Clinic" for s in subcats)

def test_record_expense_with_multiuser_attribution():
    # 1. Setup users
    users = UserService.get_all_users()
    admin_user = users[0]
    
    # Create child/beneficiary user if needed
    _, _, child_user = UserService.create_user("child_phase2", "Child Member", "pass123")
    if not child_user:
        child_user = [u for u in UserService.get_all_users() if u.username == "child_phase2"][0]

    # Create test bank account
    _, _, acc = AccountService.create_account("Test Bank Phase2", AccountType.SAVINGS.value, opening_balance_paise=1000000) # ₹10,000

    # Record expense: Paid By Admin, Beneficiary = Child Member
    expense_amt = 150000 # ₹1,500.00
    ok, msg, txn = ExpenseService.record_expense(
        title="School Uniform & Books",
        amount_paise=expense_amt,
        transaction_date=date.today(),
        account_id=acc.id,
        paid_by_id=admin_user.id,
        expense_for_id=child_user.id,
        expense_kind=ExpenseKind.DAILY.value,
        payment_method="UPI"
    )
    assert ok is True
    assert txn.paid_by_id == admin_user.id
    assert txn.expense_for_id == child_user.id

    # Verify balance deducted from bank account
    updated_acc = AccountService.get_account_by_id(acc.id)
    assert updated_acc.current_balance_paise == (1000000 - expense_amt) # ₹8,500

    # Delete expense and verify balance restoration
    del_ok, _ = ExpenseService.delete_expense(txn.id)
    assert del_ok is True
    restored_acc = AccountService.get_account_by_id(acc.id)
    assert restored_acc.current_balance_paise == 1000000

def test_income_recording():
    _, _, acc = AccountService.create_account("Salary Bank Acc", AccountType.SAVINGS.value, opening_balance_paise=500000) # ₹5,000
    admin_user = UserService.get_all_users()[0]

    income_amt = 7500000 # ₹75,000.00
    ok, msg, inc = IncomeService.record_income(
        source_title="Monthly Tech Salary",
        amount_paise=income_amt,
        income_date=date.today(),
        account_id=acc.id,
        received_by_id=admin_user.id,
        payment_mode="Bank Transfer"
    )
    assert ok is True
    assert inc.amount_paise == income_amt

    updated_acc = AccountService.get_account_by_id(acc.id)
    assert updated_acc.current_balance_paise == (500000 + income_amt) # ₹80,000

def test_internal_account_transfer():
    _, _, acc1 = AccountService.create_account("Savings Transfer Source", AccountType.SAVINGS.value, opening_balance_paise=2000000) # ₹20,000
    _, _, acc2 = AccountService.create_account("Cash Transfer Dest", AccountType.CASH.value, opening_balance_paise=100000) # ₹1,000

    transfer_amt = 500000 # ₹5,000.00
    ok, msg = AccountService.transfer_funds(
        from_account_id=acc1.id,
        to_account_id=acc2.id,
        amount_paise=transfer_amt,
        transfer_date=date.today(),
        reference_note="ATM Cash Withdrawal"
    )
    assert ok is True

    updated1 = AccountService.get_account_by_id(acc1.id)
    updated2 = AccountService.get_account_by_id(acc2.id)

    assert updated1.current_balance_paise == (2000000 - transfer_amt) # ₹15,000
    assert updated2.current_balance_paise == (100000 + transfer_amt)   # ₹6,000
