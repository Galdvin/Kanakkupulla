"""
Expense Service:
Handles daily expenses, occasional expenses, validation, attachments, duplicate prevention, and balance updates.
"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import date, datetime
from database.connection import SessionLocal
from database.models import Transaction, Account, TransactionAttachment, AuditLog
from config.constants import TransactionType, ExpenseKind, AccountType
from core.authentication import AuthService

class ExpenseService:
    @staticmethod
    def record_expense(
        title: str,
        amount_paise: int,
        transaction_date: date,
        account_id: int,
        paid_by_id: int,
        expense_for_id: int,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        payment_method: str = "Cash",
        expense_kind: str = ExpenseKind.DAILY.value,
        event_name: Optional[str] = None,
        description: Optional[str] = None,
        merchant: Optional[str] = None,
        location: Optional[str] = None,
        reference_no: Optional[str] = None,
        transaction_time: str = "12:00:00"
    ) -> Tuple[bool, str, Optional[Transaction]]:
        """
        Records a new daily or occasional expense and deducts from account balance.
        """
        if not AuthService.can_modify_transactions():
            return False, "Viewer role cannot record transactions", None

        if amount_paise <= 0:
            return False, "Expense amount must be greater than zero", None

        if not title or not title.strip():
            return False, "Expense title is required", None

        current_user = AuthService.get_current_user()
        creator_id = current_user.id if current_user else paid_by_id

        db = SessionLocal()
        try:
            # 1. Fetch Account
            account = db.query(Account).filter_by(id=account_id).first()
            if not account or not account.is_active:
                return False, "Invalid or inactive payment account", None

            # 2. Create Transaction
            txn = Transaction(
                transaction_type=TransactionType.EXPENSE.value,
                expense_kind=expense_kind,
                title=title.strip(),
                description=description.strip() if description else None,
                amount_paise=amount_paise,
                transaction_date=transaction_date,
                transaction_time=transaction_time,
                category_id=category_id,
                subcategory_id=subcategory_id,
                account_id=account_id,
                payment_method=payment_method,
                reference_no=reference_no,
                merchant=merchant,
                location=location,
                event_name=event_name.strip() if event_name else None,
                created_by_id=creator_id,
                paid_by_id=paid_by_id,
                expense_for_id=expense_for_id,
                last_modified_by_id=creator_id
            )
            db.add(txn)

            # 3. Update account balance (Subtract expense from bank/cash/wallet; for credit card, liability increases)
            if account.account_type == AccountType.CREDIT_CARD.value:
                # Credit Card liability increases (balance represents available limit or negative liability)
                account.current_balance_paise -= amount_paise
            else:
                account.current_balance_paise -= amount_paise

            # 4. Audit Log
            log = AuditLog(
                user_id=creator_id,
                action="EXPENSE_CREATED",
                entity_name="TRANSACTION",
                details=f"Recorded expense '{title}' for ₹{amount_paise/100:.2f}"
            )
            db.add(log)

            db.commit()
            db.refresh(txn)
            db.expunge(txn)
            return True, "Expense recorded successfully", txn
        except Exception as e:
            db.rollback()
            return False, f"Failed to record expense: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def get_expenses(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[int] = None,
        paid_by_id: Optional[int] = None,
        expense_for_id: Optional[int] = None,
        expense_kind: Optional[str] = None,
        event_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Transaction], int]:
        """Returns paginated filtered expenses and total count"""
        db = SessionLocal()
        try:
            q = db.query(Transaction).filter(
                Transaction.transaction_type == TransactionType.EXPENSE.value,
                Transaction.is_deleted == False
            )

            if start_date:
                q = q.filter(Transaction.transaction_date >= start_date)
            if end_date:
                q = q.filter(Transaction.transaction_date <= end_date)
            if category_id:
                q = q.filter(Transaction.category_id == category_id)
            if paid_by_id:
                q = q.filter(Transaction.paid_by_id == paid_by_id)
            if expense_for_id:
                q = q.filter(Transaction.expense_for_id == expense_for_id)
            if expense_kind:
                q = q.filter(Transaction.expense_kind == expense_kind)
            if event_name:
                q = q.filter(Transaction.event_name == event_name)

            total_count = q.count()
            results = q.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).offset(offset).limit(limit).all()
            for r in results:
                # Preload names to avoid detached errors
                _ = r.category.name if r.category else None
                _ = r.subcategory.name if r.subcategory else None
                _ = r.account.name if r.account else None
                _ = r.paid_by.full_name if r.paid_by else None
                _ = r.expense_for.full_name if r.expense_for else None
                db.expunge(r)
            return results, total_count
        finally:
            db.close()

    @staticmethod
    def delete_expense(expense_id: int) -> Tuple[bool, str]:
        """Soft deletes expense and restores account balance"""
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized action"

        current_user = AuthService.get_current_user()
        db = SessionLocal()
        try:
            txn = db.query(Transaction).filter_by(id=expense_id, is_deleted=False).first()
            if not txn or txn.transaction_type != TransactionType.EXPENSE.value:
                return False, "Expense transaction not found"

            # Reverse account balance impact
            account = db.query(Account).filter_by(id=txn.account_id).first()
            if account:
                account.current_balance_paise += txn.amount_paise

            txn.is_deleted = True
            txn.last_modified_by_id = current_user.id if current_user else None

            log = AuditLog(
                user_id=current_user.id if current_user else None,
                action="EXPENSE_DELETED",
                entity_name="TRANSACTION",
                entity_id=txn.id,
                details=f"Deleted expense ID {txn.id} ({txn.title})"
            )
            db.add(log)
            db.commit()
            return True, "Expense deleted successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()
