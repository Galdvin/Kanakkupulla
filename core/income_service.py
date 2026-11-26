"""
Income Service with Balanced Double-Entry Ledger Posting:
Credits the asset account (cash/bank) and debits the revenue source entry.
Total Debits == Total Credits.
"""
from typing import List, Optional, Tuple
from datetime import date
from database.connection import SessionLocal
from database.models import (
    FinancialTransaction, LedgerEntry, Account, FamilyMember, AuditLog
)
from config.constants import TransactionType
from core.authentication import AuthService

class IncomeService:
    @staticmethod
    def record_income(
        source_title: str,
        amount_paise: int,
        income_date: date,
        account_id: int,
        received_by_member_id: Optional[int] = None,
        description: Optional[str] = None,
        payment_mode: str = "Bank Transfer",
        reference_no: Optional[str] = None,
        received_by_id: Optional[int] = None
    ) -> Tuple[bool, str, Optional[FinancialTransaction]]:
        if not AuthService.can_modify_transactions():
            return False, "Viewer role cannot record income", None

        if amount_paise <= 0:
            return False, "Income amount must be greater than zero", None

        source_title = source_title.strip()
        if not source_title:
            return False, "Income source title is required", None

        # Resolve received_by_member_id from either parameter
        if received_by_member_id is None and received_by_id is not None:
            received_by_member_id = received_by_id

        current_user = AuthService.get_current_user()
        creator_id = current_user.id if current_user else 1

        db = SessionLocal()
        try:
            account = db.query(Account).filter_by(id=account_id).first()
            if not account or not account.is_active:
                return False, "Invalid destination account", None

            # Fallback to default primary family member if not specified
            if not received_by_member_id:
                prim_member = db.query(FamilyMember).filter_by(is_primary=True).first() or db.query(FamilyMember).first()
                if prim_member:
                    received_by_member_id = prim_member.id
                else:
                    return False, "No active family member found to attribute income", None

            txn = FinancialTransaction(
                transaction_type=TransactionType.INCOME.value,
                expense_kind="Income",
                title=source_title,
                description=description.strip() if description else None,
                amount_paise=amount_paise,
                transaction_date=income_date,
                account_id=account_id,
                payment_method=payment_mode,
                reference_no=reference_no,
                created_by_user_id=creator_id,
                paid_by_member_id=received_by_member_id,
                expense_for_member_id=received_by_member_id,
                last_modified_by_id=creator_id
            )
            db.add(txn)
            db.flush()

            # Balanced Double-Entry Journal:
            # Entry 1: DEBIT the Asset Account (Cash/Bank increases)
            debit_entry = LedgerEntry(
                transaction_id=txn.id,
                account_id=account.id,
                entry_type="DEBIT",
                amount_paise=amount_paise,
                entry_date=income_date,
                description=f"Received Income: {source_title}"
            )
            db.add(debit_entry)

            # Entry 2: CREDIT the Income Source
            credit_entry = LedgerEntry(
                transaction_id=txn.id,
                account_id=account.id,
                entry_type="CREDIT",
                amount_paise=amount_paise,
                entry_date=income_date,
                description=f"Revenue Credit: {source_title}"
            )
            db.add(credit_entry)

            # Credit designated account current balance
            account.current_balance_paise += amount_paise

            # Audit
            log = AuditLog(
                user_id=creator_id,
                action="INCOME_RECORDED",
                entity_name="TRANSACTION",
                entity_id=txn.id,
                details=f"Recorded income '{source_title}' of ₹{amount_paise/100:.2f}"
            )
            db.add(log)

            db.commit()
            db.refresh(txn)
            _ = txn.account.name if txn.account else None
            _ = txn.paid_by_member.name if txn.paid_by_member else None
            db.expunge(txn)
            return True, "Income recorded successfully", txn
        except Exception as e:
            db.rollback()
            return False, f"Failed: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def get_incomes(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        received_by_member_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[FinancialTransaction], int]:
        db = SessionLocal()
        try:
            q = db.query(FinancialTransaction).filter(
                FinancialTransaction.transaction_type == TransactionType.INCOME.value,
                FinancialTransaction.is_deleted == False
            )
            if start_date:
                q = q.filter(FinancialTransaction.transaction_date >= start_date)
            if end_date:
                q = q.filter(FinancialTransaction.transaction_date <= end_date)
            if received_by_member_id:
                q = q.filter(FinancialTransaction.paid_by_member_id == received_by_member_id)

            total_count = q.count()
            results = q.order_by(FinancialTransaction.transaction_date.desc(), FinancialTransaction.id.desc()).offset(offset).limit(limit).all()
            for r in results:
                _ = r.account.name if r.account else None
                _ = r.paid_by_member.name if r.paid_by_member else None
                db.expunge(r)
            return results, total_count
        finally:
            db.close()
