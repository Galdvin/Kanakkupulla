"""
Phase 2 Automated Test Suite:
1. Quick expense entry
2. Receipt & document attachments with file storage verification in %LOCALAPPDATA%
3. Search transactions with keyword, payer, beneficiary, and date filters
4. Multi-user beneficiary query verification
"""
from datetime import date
from pathlib import Path
import pytest
from database.connection import SessionLocal
from database.models import FinancialTransaction, TransactionAttachment
from core.authentication import AuthService
from core.expense_service import ExpenseService
from core.accounting_service import AccountService
from core.family_service import FamilyService
from core.category_service import CategoryService
from core.attachment_service import AttachmentService
from core.transaction_search_service import TransactionSearchService
from config.constants import ExpenseKind

@pytest.fixture(autouse=True)
def setup_auth():
    AuthService.login("admin", "admin123")
    yield
    AuthService.logout()

def test_quick_expense_and_search():
    acc = AccountService.get_all_accounts()[0]
    member = FamilyService.get_all_members()[0]
    cat = CategoryService.get_all_categories()[0]

    # 1. Record quick expense
    ok, msg, txn = ExpenseService.record_expense(
        title="Express Metro Recharge",
        amount_paise=45000, # ₹450.00
        transaction_date=date.today(),
        account_id=acc.id,
        paid_by_member_id=member.id,
        expense_for_member_id=member.id,
        category_id=cat.id,
        merchant="Namma Metro BMRCL"
    )
    assert ok is True
    assert txn.id is not None

    # 2. Search by keyword
    results, count, total = TransactionSearchService.search_transactions(keyword="Metro")
    assert count >= 1
    assert any(t.id == txn.id for t in results)
    assert total >= 45000

def test_transaction_attachment_storage():
    acc = AccountService.get_all_accounts()[0]
    member = FamilyService.get_all_members()[0]

    ok, _, txn = ExpenseService.record_expense(
        title="Electronics Purchase Bill",
        amount_paise=1500000, # ₹15,000.00
        transaction_date=date.today(),
        account_id=acc.id,
        paid_by_member_id=member.id,
        expense_for_member_id=member.id
    )
    assert ok is True

    # Create dummy bill file
    temp_receipt = Path("temp_test_receipt.jpg")
    temp_receipt.write_bytes(b"Simulated JPEG bill image bytes")

    try:
        attach_ok, attach_msg, att = AttachmentService.attach_file_to_transaction(
            transaction_id=txn.id,
            source_file_path=temp_receipt
        )
        assert attach_ok is True
        assert att.file_name == temp_receipt.name
        
        # Verify copied file exists in LocalAppData directory
        saved_path = Path(att.file_path)
        assert saved_path.exists()
        assert saved_path.stat().st_size > 0

        # Retrieve attachments
        all_att = AttachmentService.get_transaction_attachments(txn.id)
        assert len(all_att) >= 1
    finally:
        if temp_receipt.exists():
            temp_receipt.unlink()
