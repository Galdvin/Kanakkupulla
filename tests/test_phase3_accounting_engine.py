"""
Phase 3 Automated Test Suite:
1. Credit Card purchase vs Bill Payment Rule 2 check:
   - CC purchase creates expense and posts Debit(Expense) & Credit(CC Liability)
   - CC bill settlement posts Debit(CC Liability) & Credit(Bank Asset) WITHOUT creating an expense
2. General ledger double-entry integrity check across multiple transactions
3. Audit log retrieval and recording
"""
from datetime import date
import pytest
from core.authentication import AuthService
from core.accounting_service import AccountService
from core.expense_service import ExpenseService
from core.accounting_service_engine import AccountingEngineService
from core.family_service import FamilyService
from config.constants import AccountType

@pytest.fixture(autouse=True)
def setup_auth():
    AuthService.login("admin", "admin123")
    yield
    AuthService.logout()

def test_credit_card_purchase_and_bill_payment_rule2():
    """
    Rule 2: Credit Card Purchase ₹2,000 is an expense.
    Paying the ₹2,000 Credit Card bill later must reduce liability without creating an expense.
    """
    # 1. Create Bank and Credit Card
    _, _, bank = AccountService.create_account("HDFC Bank Primary", AccountType.SAVINGS.value, opening_balance_paise=5000000) # ₹50,000
    _, _, cc = AccountService.create_account("Amazon ICICI Card", AccountType.CREDIT_CARD.value, opening_balance_paise=0, credit_limit_paise=10000000) # ₹1,00,000 limit
    member = FamilyService.get_all_members()[0]

    # 2. Credit Card Purchase of ₹2,000
    purchase_amt = 200000 # ₹2,000.00
    ok_exp, _, txn_exp = ExpenseService.record_expense(
        title="Dinner Buffet",
        amount_paise=purchase_amt,
        transaction_date=date.today(),
        account_id=cc.id,
        paid_by_member_id=member.id,
        expense_for_member_id=member.id,
        payment_method="Credit Card"
    )
    assert ok_exp is True

    # Check CC liability increased (balance reduced)
    cc_after_purchase = AccountService.get_account_by_id(cc.id)
    assert cc_after_purchase.current_balance_paise == -200000

    # 3. Pay the Credit Card bill of ₹2,000 from Bank
    ok_pay, _, txn_pay = AccountingEngineService.process_credit_card_bill_payment(
        bank_account_id=bank.id,
        credit_card_account_id=cc.id,
        payment_amount_paise=purchase_amt,
        payment_date=date.today(),
        reference_no="CC-STMT-NOV26"
    )
    assert ok_pay is True

    # Verify Bank asset reduced by ₹2,000
    bank_after_pay = AccountService.get_account_by_id(bank.id)
    assert bank_after_pay.current_balance_paise == (5000000 - purchase_amt) # ₹48,000

    # Verify CC liability cleared back to 0
    cc_after_pay = AccountService.get_account_by_id(cc.id)
    assert cc_after_pay.current_balance_paise == 0

    # 4. Verify Accounting Equation Integrity
    integrity = AccountingEngineService.verify_ledger_integrity()
    assert integrity["is_system_balanced"] is True
    assert integrity["unbalanced_transaction_count"] == 0

def test_audit_trail_logging():
    logs = AccountingEngineService.get_audit_trail(limit=20)
    assert len(logs) >= 1
    actions = [l.action for l in logs]
    assert any("RECORDED" in a or "LOGIN" in a or "CREATED" in a or "PAID" in a for a in actions)
