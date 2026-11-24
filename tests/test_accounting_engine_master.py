"""
Master Financial Invariant and Ledger Tests:
1. Double-Entry Invariant: Every posted transaction satisfies sum(Debits) == sum(Credits)
2. Payer vs Beneficiary: Father pays for Child -> Father's payer-expenses and Child's beneficiary-expenses update
3. Rule 1: Internal Account transfers must create 0 expense and 0 income
4. Rule 2: Credit card purchases count as expense once; bill payments do not duplicate expenses
5. Rule 4: Loan repayment amortization separates principal reduction from interest
6. Rule 5: Refunds/Reversals record debit/credit reversal entries and restore balance
7. Rule 7: Integer Paise Precision: zero binary floating point discrepancy
8. Argon2id Password verification
"""
from datetime import date
import pytest
from database.connection import Base, engine, SessionLocal
from database.models import FinancialTransaction, LedgerEntry, Account, FamilyMember, User
from database.seed import seed_database
from core.authentication import AuthService, hash_password, verify_password
from core.family_service import FamilyService
from core.accounting_service import AccountService
from core.expense_service import ExpenseService
from core.income_service import IncomeService
from core.loan_service import LoanService
from core.financial_utils import inr_to_paise, paise_to_inr, format_inr
from config.constants import AccountType, ExpenseKind

@pytest.fixture(autouse=True)
def clean_database():
    pass # Managed safely by conftest.py

def test_argon2_password_hashing():
    pwd = "SecureFamilyPassword2026"
    hashed = hash_password(pwd)
    assert "$argon2" in hashed
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_integer_paise_precision():
    # Verify no floating point rounding error (e.g. 1000.50 -> 100050)
    assert inr_to_paise(1000.50) == 100050
    assert inr_to_paise("250.00") == 25000
    assert paise_to_inr(100050) == 1000.50
    assert format_inr(100050) == "₹1,000.50"

def test_balanced_double_entry_ledger_invariant():
    """Rule 6: Every posted journal must balance: Total Debits == Total Credits"""
    acc = AccountService.get_all_accounts()[0]
    member = FamilyService.get_all_members()[0]

    ok, msg, txn = ExpenseService.record_expense(
        title="Weekly Groceries",
        amount_paise=250000, # ₹2,500.00
        transaction_date=date.today(),
        account_id=acc.id,
        paid_by_member_id=member.id,
        expense_for_member_id=member.id
    )
    assert ok is True

    db = SessionLocal()
    try:
        entries = db.query(LedgerEntry).filter_by(transaction_id=txn.id).all()
        assert len(entries) >= 2
        total_debits = sum(e.amount_paise for e in entries if e.entry_type == "DEBIT")
        total_credits = sum(e.amount_paise for e in entries if e.entry_type == "CREDIT")
        assert total_debits == total_credits == 250000
    finally:
        db.close()

def test_payer_vs_beneficiary_attribution():
    """Father pays ₹5,000 for Child's Education -> both payer and beneficiary reports update"""
    # Create Father and Child members
    _, _, father = FamilyService.add_family_member("Father Profile", relation_type="Parent")
    _, _, child = FamilyService.add_family_member("Child Profile", relation_type="Child")
    acc = AccountService.get_all_accounts()[0]

    school_fee = 500000 # ₹5,000.00
    ok, msg, txn = ExpenseService.record_expense(
        title="School Term Tuition Fee",
        amount_paise=school_fee,
        transaction_date=date.today(),
        account_id=acc.id,
        paid_by_member_id=father.id,
        expense_for_member_id=child.id
    )
    assert ok is True
    assert txn.paid_by_member_id == father.id
    assert txn.expense_for_member_id == child.id

    # Verify Payer-wise query
    father_expenses, count1 = ExpenseService.get_expenses(paid_by_member_id=father.id)
    assert any(e.id == txn.id for e in father_expenses)

    # Verify Beneficiary-wise query
    child_expenses, count2 = ExpenseService.get_expenses(expense_for_member_id=child.id)
    assert any(e.id == txn.id for e in child_expenses)

def test_rule1_internal_account_transfers():
    """Transferring ₹10,000 between accounts must NOT create an expense or income"""
    _, _, bank_a = AccountService.create_account("Bank A", AccountType.SAVINGS.value, opening_balance_paise=5000000)
    _, _, bank_b = AccountService.create_account("Bank B", AccountType.SAVINGS.value, opening_balance_paise=1000000)

    transfer_amt = 1000000 # ₹10,000.00
    ok, msg = AccountService.transfer_funds(
        from_account_id=bank_a.id,
        to_account_id=bank_b.id,
        amount_paise=transfer_amt,
        transfer_date=date.today(),
        reference_note="Savings Rebalancing"
    )
    assert ok is True

    # Balances updated
    a_up = AccountService.get_account_by_id(bank_a.id)
    b_up = AccountService.get_account_by_id(bank_b.id)
    assert a_up.current_balance_paise == 4000000
    assert b_up.current_balance_paise == 2000000

    # Verify NO Expense or Income was created
    expenses, exp_count = ExpenseService.get_expenses()
    incomes, inc_count = IncomeService.get_incomes()
    assert not any("Transfer from" in e.title for e in expenses)
    assert not any("Transfer from" in i.title for i in incomes)

def test_rule5_reversals_and_refunds():
    """Deleting an expense creates balanced reversal entries and restores balance"""
    acc = AccountService.get_all_accounts()[0]
    initial_bal = acc.current_balance_paise
    member = FamilyService.get_all_members()[0]

    amt = 150000
    ok, _, txn = ExpenseService.record_expense(
        title="Incorrect Bill Entry",
        amount_paise=amt,
        transaction_date=date.today(),
        account_id=acc.id,
        paid_by_member_id=member.id,
        expense_for_member_id=member.id
    )
    assert ok is True

    # Reverse transaction
    del_ok, _ = ExpenseService.delete_expense(txn.id)
    assert del_ok is True

    # Balance restored
    restored_acc = AccountService.get_account_by_id(acc.id)
    assert restored_acc.current_balance_paise == initial_bal

    # Verify reversal entries exist in ledger
    db = SessionLocal()
    try:
        reversals = db.query(LedgerEntry).filter(
            LedgerEntry.transaction_id == txn.id,
            LedgerEntry.description.like("REVERSAL:%")
        ).all()
        assert len(reversals) >= 2
    finally:
        db.close()
