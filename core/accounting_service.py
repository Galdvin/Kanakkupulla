"""
Bank Account and Payment Management Service
Handles Accounts (Cash, Savings, Current, Credit Cards, Wallets),
Balance recalculation, and inter-account Transfers (strictly distinct from income/expenses).
"""
from typing import List, Optional, Tuple
from datetime import date
from database.connection import SessionLocal
from database.models import Account, AccountTransfer, Transaction, AuditLog
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
                return False, f"Account '{name}' already exists", None

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
        reference_note: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Executes an internal account transfer.
        Accounting rule: Internal transfers must NEVER be counted as expense or income.
        """
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized"

        if from_account_id == to_account_id:
            return False, "Source and destination accounts must be different"

        if amount_paise <= 0:
            return False, "Transfer amount must be greater than zero"

        current_user = AuthService.get_current_user()
        db = SessionLocal()
        try:
            from_acc = db.query(Account).filter_by(id=from_account_id).first()
            to_acc = db.query(Account).filter_by(id=to_account_id).first()

            if not from_acc or not to_acc or not from_acc.is_active or not to_acc.is_active:
                return False, "One or both accounts are invalid or inactive"

            # Execute balance movements
            from_acc.current_balance_paise -= amount_paise
            to_acc.current_balance_paise += amount_paise

            # Record transfer record
            transfer = AccountTransfer(
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                amount_paise=amount_paise,
                transfer_date=transfer_date,
                reference_note=reference_note,
                created_by_id=current_user.id if current_user else 1
            )
            db.add(transfer)

            log = AuditLog(
                user_id=current_user.id if current_user else None,
                action="ACCOUNT_TRANSFER",
                entity_name="TRANSFER",
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

    @staticmethod
    def pay_credit_card_bill(
        bank_account_id: int,
        credit_card_account_id: int,
        payment_amount_paise: int,
        payment_date: date,
        reference: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Pays credit card bill from bank account.
        Accounting rule: Decreases bank balance and decreases CC liability (increases CC balance/available limit)
        WITHOUT double-counting historical CC purchases as an expense again.
        """
        return AccountService.transfer_funds(
            from_account_id=bank_account_id,
            to_account_id=credit_card_account_id,
            amount_paise=payment_amount_paise,
            transfer_date=payment_date,
            reference_note=f"Credit Card Bill Payment {reference or ''}".strip()
        )
