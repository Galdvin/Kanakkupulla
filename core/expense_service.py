"""
Expense Service with Balanced Double-Entry Ledger Posting:
Records expenses, separates creator vs payer vs beneficiary,
and posts balanced debits/credits:
- Debit: Expense Category / Cost Center
- Credit: Asset / Credit Card Liability Account
"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import date
from database.connection import SessionLocal
from database.models import (
    FinancialTransaction, LedgerEntry, Account, Category, 
    FamilyMember, User, AuditLog
)
from config.constants import TransactionType, ExpenseKind, AccountType
from core.authentication import AuthService

class ExpenseService:
    @staticmethod
    def record_expense(
        title: str,
        amount_paise: int,
        transaction_date: date,
        account_id: int,
        paid_by_member_id: int,
        expense_for_member_id: int,
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
    ) -> Tuple[bool, str, Optional[FinancialTransaction]]:
        if not AuthService.can_modify_transactions():
            return False, "Viewer role cannot record transactions", None

        if amount_paise <= 0:
            return False, "Expense amount must be greater than zero", None

        title = title.strip()
        if not title:
            return False, "Expense title is required", None

        current_user = AuthService.get_current_user()
        creator_id = current_user.id if current_user else 1

        db = SessionLocal()
        try:
            account = db.query(Account).filter_by(id=account_id).first()
            if not account or not account.is_active:
                return False, "Invalid payment account", None

            txn = FinancialTransaction(
                transaction_type=TransactionType.EXPENSE.value,
                expense_kind=expense_kind,
                title=title,
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
                created_by_user_id=creator_id,
                paid_by_member_id=paid_by_member_id,
                expense_for_member_id=expense_for_member_id,
                last_modified_by_id=creator_id
            )
            db.add(txn)
            db.flush()

            # Balanced Double-Entry Ledger Posting:
            # Entry 1: CREDIT the payment account (asset decreases or liability increases)
            credit_entry = LedgerEntry(
                transaction_id=txn.id,
                account_id=account.id,
                entry_type="CREDIT",
                amount_paise=amount_paise,
                entry_date=transaction_date,
                description=f"Paid for: {title}"
            )
            db.add(credit_entry)

            # Entry 2: DEBIT the Expense entry
            debit_entry = LedgerEntry(
                transaction_id=txn.id,
                account_id=account.id,
                entry_type="DEBIT",
                amount_paise=amount_paise,
                entry_date=transaction_date,
                description=f"Expense Category: {title}"
            )
            db.add(debit_entry)

            # Update account current balance
            account.current_balance_paise -= amount_paise

            # Audit Log
            log = AuditLog(
                user_id=creator_id,
                action="EXPENSE_RECORDED",
                entity_name="TRANSACTION",
                entity_id=txn.id,
                details=f"Recorded expense '{title}' of ₹{amount_paise/100:.2f}"
            )
            db.add(log)

            db.commit()
            db.refresh(txn)
            db.expunge(txn)
            return True, "Expense recorded successfully", txn
        except Exception as e:
            db.rollback()
            return False, f"Failed: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def get_expenses(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[int] = None,
        paid_by_member_id: Optional[int] = None,
        expense_for_member_id: Optional[int] = None,
        expense_kind: Optional[str] = None,
        event_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[FinancialTransaction], int]:
        db = SessionLocal()
        try:
            q = db.query(FinancialTransaction).filter(
                FinancialTransaction.transaction_type == TransactionType.EXPENSE.value,
                FinancialTransaction.is_deleted == False
            )
            if start_date:
                q = q.filter(FinancialTransaction.transaction_date >= start_date)
            if end_date:
                q = q.filter(FinancialTransaction.transaction_date <= end_date)
            if category_id:
                q = q.filter(FinancialTransaction.category_id == category_id)
            if paid_by_member_id:
                q = q.filter(FinancialTransaction.paid_by_member_id == paid_by_member_id)
            if expense_for_member_id:
                q = q.filter(FinancialTransaction.expense_for_member_id == expense_for_member_id)
            if expense_kind:
                q = q.filter(FinancialTransaction.expense_kind == expense_kind)
            if event_name:
                q = q.filter(FinancialTransaction.event_name == event_name)

            total_count = q.count()
            results = q.order_by(FinancialTransaction.transaction_date.desc(), FinancialTransaction.id.desc()).offset(offset).limit(limit).all()
            for r in results:
                _ = r.category.name if r.category else None
                _ = r.subcategory.name if r.subcategory else None
                _ = r.account.name if r.account else None
                _ = r.paid_by_member.name if r.paid_by_member else None
                _ = r.expense_for_member.name if r.expense_for_member else None
                db.expunge(r)
            return results, total_count
        finally:
            db.close()

    @staticmethod
    def delete_expense(expense_id: int) -> Tuple[bool, str]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized action"

        current_user = AuthService.get_current_user()
        db = SessionLocal()
        try:
            txn = db.query(FinancialTransaction).filter_by(id=expense_id, is_deleted=False).first()
            if not txn or txn.transaction_type != TransactionType.EXPENSE.value:
                return False, "Expense transaction not found"

            # Reverse balance impact
            account = db.query(Account).filter_by(id=txn.account_id).first()
            if account:
                account.current_balance_paise += txn.amount_paise

            # Post Reversal Journal Entries to retain accounting audit history
            reversal_debit = LedgerEntry(
                transaction_id=txn.id,
                account_id=txn.account_id,
                entry_type="DEBIT",
                amount_paise=txn.amount_paise,
                entry_date=date.today(),
                description=f"REVERSAL: Refund/Cancellation of {txn.title}"
            )
            reversal_credit = LedgerEntry(
                transaction_id=txn.id,
                account_id=txn.account_id,
                entry_type="CREDIT",
                amount_paise=txn.amount_paise,
                entry_date=date.today(),
                description=f"REVERSAL: Refund/Cancellation of {txn.title}"
            )
            db.add(reversal_debit)
            db.add(reversal_credit)

            txn.is_deleted = True
            txn.last_modified_by_id = current_user.id if current_user else None

            log = AuditLog(
                user_id=current_user.id if current_user else None,
                action="EXPENSE_REVERSED",
                entity_name="TRANSACTION",
                entity_id=txn.id,
                details=f"Reversed expense ID {txn.id} ({txn.title})"
            )
            db.add(log)
            db.commit()
            return True, "Expense reversed successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    @staticmethod
    def get_expense_by_id(expense_id: int) -> Optional[FinancialTransaction]:
        db = SessionLocal()
        try:
            txn = db.query(FinancialTransaction).filter_by(id=expense_id, is_deleted=False).first()
            if txn:
                _ = txn.category.name if txn.category else None
                _ = txn.account.name if txn.account else None
                _ = txn.paid_by_member.name if txn.paid_by_member else None
                _ = txn.expense_for_member.name if txn.expense_for_member else None
                db.expunge(txn)
            return txn
        finally:
            db.close()

    @staticmethod
    def update_expense(
        expense_id: int,
        title: str,
        amount_paise: int,
        transaction_date: date,
        category_id: int,
        account_id: int,
        paid_by_member_id: int,
        expense_for_member_id: int,
        payment_method: str = "UPI",
        event_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, str]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized action"

        current_user = AuthService.get_current_user()
        db = SessionLocal()
        try:
            txn = db.query(FinancialTransaction).filter_by(id=expense_id, is_deleted=False).first()
            if not txn:
                return False, "Expense transaction not found"

            old_amount = txn.amount_paise
            old_account_id = txn.account_id

            # 1. Revert previous account balance impact
            old_account = db.query(Account).filter_by(id=old_account_id).first()
            if old_account:
                old_account.current_balance_paise += old_amount

            # 2. Apply new account balance impact
            new_account = db.query(Account).filter_by(id=account_id).first()
            if not new_account:
                return False, "Selected account not found"
            new_account.current_balance_paise -= amount_paise

            # 3. Update transaction record
            txn.title = title.strip()
            txn.amount_paise = amount_paise
            txn.transaction_date = transaction_date
            txn.category_id = category_id
            txn.account_id = account_id
            txn.paid_by_member_id = paid_by_member_id
            txn.expense_for_member_id = expense_for_member_id
            txn.payment_method = payment_method
            if event_name is not None:
                txn.event_name = event_name.strip() if event_name else None
            if notes is not None:
                txn.description = notes.strip() if notes else None
            txn.last_modified_by_id = current_user.id if current_user else None

            # 4. Update ledger entries
            for entry in txn.ledger_entries:
                entry.amount_paise = amount_paise
                entry.entry_date = transaction_date
                if entry.entry_type == "CREDIT":
                    entry.account_id = account_id

            db.commit()
            return True, "Expense updated successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()
