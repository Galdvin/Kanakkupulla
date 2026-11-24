"""
Income Service:
Handles income tracking from diverse sources (Salary, Freelance, Business, Dividends, etc.),
crediting to designated bank accounts/wallets, and multi-user attribution.
"""
from typing import List, Optional, Tuple
from datetime import date
from database.connection import SessionLocal
from database.models import Transaction, Account, AuditLog
from config.constants import TransactionType
from core.authentication import AuthService

class IncomeService:
    @staticmethod
    def record_income(
        source_title: str,
        amount_paise: int,
        income_date: date,
        account_id: int,
        received_by_id: int,
        description: Optional[str] = None,
        payment_mode: str = "Bank Transfer",
        reference_no: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Transaction]]:
        if not AuthService.can_modify_transactions():
            return False, "Viewer role cannot record income", None

        if amount_paise <= 0:
            return False, "Income amount must be greater than zero", None

        source_title = source_title.strip()
        if not source_title:
            return False, "Income source title is required", None

        current_user = AuthService.get_current_user()
        creator_id = current_user.id if current_user else received_by_id

        db = SessionLocal()
        try:
            account = db.query(Account).filter_by(id=account_id).first()
            if not account or not account.is_active:
                return False, "Invalid destination account", None

            txn = Transaction(
                transaction_type=TransactionType.INCOME.value,
                expense_kind="Income",
                title=source_title,
                description=description.strip() if description else None,
                amount_paise=amount_paise,
                transaction_date=income_date,
                account_id=account_id,
                payment_method=payment_mode,
                reference_no=reference_no,
                created_by_id=creator_id,
                paid_by_id=received_by_id,     # Source/Earner
                expense_for_id=received_by_id, # Credited beneficiary
                last_modified_by_id=creator_id
            )
            db.add(txn)

            # Credit to designated account
            account.current_balance_paise += amount_paise

            log = AuditLog(
                user_id=creator_id,
                action="INCOME_RECORDED",
                entity_name="TRANSACTION",
                details=f"Recorded income '{source_title}' of ₹{amount_paise/100:.2f}"
            )
            db.add(log)

            db.commit()
            db.refresh(txn)
            db.expunge(txn)
            return True, "Income recorded successfully", txn
        except Exception as e:
            db.rollback()
            return False, f"Failed to record income: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def get_incomes(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        received_by_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Transaction], int]:
        db = SessionLocal()
        try:
            q = db.query(Transaction).filter(
                Transaction.transaction_type == TransactionType.INCOME.value,
                Transaction.is_deleted == False
            )
            if start_date:
                q = q.filter(Transaction.transaction_date >= start_date)
            if end_date:
                q = q.filter(Transaction.transaction_date <= end_date)
            if received_by_id:
                q = q.filter(Transaction.paid_by_id == received_by_id)

            total_count = q.count()
            results = q.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).offset(offset).limit(limit).all()
            for r in results:
                _ = r.account.name if r.account else None
                _ = r.paid_by.full_name if r.paid_by else None
                db.expunge(r)
            return results, total_count
        finally:
            db.close()
