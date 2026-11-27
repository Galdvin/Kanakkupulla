"""
Bank Account and Payment Management Service with Balanced Double-Entry Ledgers:
Handles internal transfers between owned accounts and credit card bill payments.
Ensures zero expense or income is created for internal fund transfers.
"""
from typing import List, Optional, Tuple
from datetime import date
from database.connection import SessionLocal
from database.models import Account, FinancialTransaction, LedgerEntry, AuditLog
from config.constants import AccountType, TransactionType
from core.authentication import AuthService

class AccountService:
    @staticmethod
    def get_all_accounts(active_only: bool = True) -> List[Account]:
        db = SessionLocal()
        try:
            q = db.query(Account)
            if active_only:
                q = q.filter_by(is_active=True)
            results = q.order_by(Account.account_type, Account.name).all()
            for acc in results:
                db.expunge(acc)
            return results
        finally:
            db.close()

    @staticmethod
    def get_account_by_id(account_id: int) -> Optional[Account]:
        db = SessionLocal()
        try:
            acc = db.query(Account).filter_by(id=account_id).first()
            if acc:
                db.expunge(acc)
            return acc
        finally:
            db.close()

    @staticmethod
    def create_account(
        name: str,
        account_type: str,
        opening_balance_paise: int = 0,
        credit_limit_paise: int = 0,
        institution_name: Optional[str] = None,
        account_number_masked: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Account]]:
        name = name.strip()
        if not name:
            return False, "Account name is required", None

        db = SessionLocal()
        try:
            existing = db.query(Account).filter_by(name=name).first()
            if existing:
                db.expunge(existing)
                return True, "Account already exists", existing

            acc = Account(
                name=name,
                account_type=account_type,
                opening_balance_paise=opening_balance_paise,
                current_balance_paise=opening_balance_paise,
                credit_limit_paise=credit_limit_paise,
                institution_name=institution_name,
                account_number_masked=account_number_masked,
                notes=notes,
                is_active=True
            )
            db.add(acc)
            db.commit()
            db.refresh(acc)
            db.expunge(acc)
            return True, "Account created successfully", acc
        except Exception as e:
            db.rollback()
            return False, str(e), None
        finally:
            db.close()

    @staticmethod
    def transfer_funds(
        from_account_id: int,
        to_account_id: int,
        amount_paise: int,
        transfer_date: date,
        reference_note: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Executes internal account transfer using balanced double-entry accounting.
        Rule 1: Never creates an expense or income entry.
        Debit Destination Account (Asset Increases), Credit Source Account (Asset Decreases).
        """
        reference_note = reference_note or notes
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized"

        if from_account_id == to_account_id:
            return False, "Source and destination accounts must be different"

        if amount_paise <= 0:
            return False, "Transfer amount must be greater than zero"

        current_user = AuthService.get_current_user()
        creator_id = current_user.id if current_user else 1

        db = SessionLocal()
        try:
            from_acc = db.query(Account).filter_by(id=from_account_id).first()
            to_acc = db.query(Account).filter_by(id=to_account_id).first()

            if not from_acc or not to_acc or not from_acc.is_active or not to_acc.is_active:
                return False, "One or both accounts are invalid or inactive"

            # Create Master Transfer Transaction
            txn = FinancialTransaction(
                transaction_type=TransactionType.TRANSFER.value,
                expense_kind="Transfer",
                title=f"Transfer from {from_acc.name} to {to_acc.name}",
                description=reference_note,
                amount_paise=amount_paise,
                transaction_date=transfer_date,
                account_id=from_account_id,
                payment_method="Account Transfer",
                reference_no=reference_note,
                created_by_user_id=creator_id,
                paid_by_member_id=1,
                expense_for_member_id=1
            )
            db.add(txn)
            db.flush()

            # Balanced Double-Entry Postings:
            # Entry 1: CREDIT Source Account (Asset decreases)
            credit_entry = LedgerEntry(
                transaction_id=txn.id,
                account_id=from_account_id,
                entry_type="CREDIT",
                amount_paise=amount_paise,
                entry_date=transfer_date,
                description=f"Transfer OUT to {to_acc.name}"
            )
            db.add(credit_entry)

            # Entry 2: DEBIT Destination Account (Asset increases)
            debit_entry = LedgerEntry(
                transaction_id=txn.id,
                account_id=to_account_id,
                entry_type="DEBIT",
                amount_paise=amount_paise,
                entry_date=transfer_date,
                description=f"Transfer IN from {from_acc.name}"
            )
            db.add(debit_entry)

            # Adjust account balances
            from_acc.current_balance_paise -= amount_paise
            to_acc.current_balance_paise += amount_paise

            log = AuditLog(
                user_id=creator_id,
                action="ACCOUNT_TRANSFER",
                entity_name="TRANSFER",
                entity_id=txn.id,
                details=f"Transferred ₹{amount_paise/100:.2f} from {from_acc.name} to {to_acc.name}"
            )
            db.add(log)

            db.commit()
            return True, "Transfer executed successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    # Convenience aliases
    record_transfer = transfer_funds

    @staticmethod
    def pay_credit_card_bill(
        from_account_id: int,
        card_account_id: int,
        amount_paise: int,
        payment_date: date,
        reference: Optional[str] = None
    ) -> Tuple[bool, str]:
        from core.accounting_service_engine import AccountingEngineService
        ok, msg, _ = AccountingEngineService.process_credit_card_bill_payment(
            bank_account_id=from_account_id,
            credit_card_account_id=card_account_id,
            payment_amount_paise=amount_paise,
            payment_date=payment_date,
            reference_no=reference
        )
        return ok, msg

    @staticmethod
    def update_account(
        account_id: int,
        name: str,
        account_type: str,
        institution_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, str]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized action"

        db = SessionLocal()
        try:
            acc = db.query(Account).filter_by(id=account_id).first()
            if not acc:
                return False, "Account not found"
            acc.name = name.strip()
            acc.account_type = account_type
            acc.institution_name = institution_name.strip() if institution_name else None
            acc.notes = notes.strip() if notes else None
            db.commit()
            return True, "Account updated successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    @staticmethod
    def delete_account(account_id: int) -> Tuple[bool, str]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized action"

        db = SessionLocal()
        try:
            acc = db.query(Account).filter_by(id=account_id).first()
            if not acc:
                return False, "Account not found"
            acc.is_active = False
            db.commit()
            return True, "Account deactivated successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()


# Module export aliases
AccountingService = AccountService
__all__ = ["AccountService", "AccountingService"]

