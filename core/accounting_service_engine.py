"""
Accounting Service (Phase 3 Engine):
Implements:
1. Double-Entry General Ledger reconciliation and balance integrity checks:
   sum(Debits) == sum(Credits)
2. Account reconciliation (Statement Balance vs System Balance)
3. Audit history query service
4. Refund linkage and accounting reversals
5. Credit Card purchase vs Bill Payment processing
"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import date
from database.connection import SessionLocal
from database.models import (
    FinancialTransaction, LedgerEntry, Account, AuditLog
)
from config.constants import TransactionType, AccountType
from core.authentication import AuthService

class AccountingEngineService:
    @staticmethod
    def get_general_ledger_entries(
        account_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 150,
        offset: int = 0
    ) -> Tuple[List[LedgerEntry], int, Dict[str, int]]:
        """
        Retrieves double-entry ledger journals.
        Returns: (entries, total_count, {"total_debits": int, "total_credits": int})
        """
        db = SessionLocal()
        try:
            q = db.query(LedgerEntry)
            if account_id:
                q = q.filter(LedgerEntry.account_id == account_id)
            if start_date:
                q = q.filter(LedgerEntry.entry_date >= start_date)
            if end_date:
                q = q.filter(LedgerEntry.entry_date <= end_date)

            total_count = q.count()
            all_entries = q.all()
            total_debits = sum(e.amount_paise for e in all_entries if e.entry_type == "DEBIT")
            total_credits = sum(e.amount_paise for e in all_entries if e.entry_type == "CREDIT")

            paginated = q.order_by(LedgerEntry.entry_date.desc(), LedgerEntry.id.desc()).offset(offset).limit(limit).all()
            for entry in paginated:
                _ = entry.account.name if entry.account else None
                _ = entry.transaction.title if entry.transaction else None
                db.expunge(entry)

            return paginated, total_count, {
                "total_debits": total_debits,
                "total_credits": total_credits,
                "is_balanced": total_debits == total_credits
            }
        finally:
            db.close()

    @staticmethod
    def get_bank_passbook_entries(
        account_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 150,
        offset: int = 0
    ) -> Tuple[List[FinancialTransaction], int, Dict[str, Any]]:
        """
        Retrieves user-friendly retail bank passbook / statement entries.
        In consumer banking:
        - Outflows / Expenses = DEBITS (-)
        - Inflows / Salary / Deposits = CREDITS (+)
        """
        db = SessionLocal()
        try:
            q = db.query(FinancialTransaction).filter(FinancialTransaction.is_deleted == False)
            if account_id:
                q = q.filter(FinancialTransaction.account_id == account_id)
            if start_date:
                q = q.filter(FinancialTransaction.transaction_date >= start_date)
            if end_date:
                q = q.filter(FinancialTransaction.transaction_date <= end_date)

            total_count = q.count()
            all_txns = q.all()

            total_debits = 0   # Expenses / Outflows
            total_credits = 0  # Income / Deposits

            for t in all_txns:
                if t.transaction_type == TransactionType.INCOME.value:
                    total_credits += t.amount_paise
                elif t.transaction_type in (TransactionType.EXPENSE.value, TransactionType.CREDIT_PAYMENT.value):
                    total_debits += t.amount_paise

            paginated = q.order_by(FinancialTransaction.transaction_date.desc(), FinancialTransaction.id.desc()).offset(offset).limit(limit).all()
            for t in paginated:
                _ = t.account.name if t.account else None
                _ = t.category.name if t.category else None
                db.expunge(t)

            return paginated, total_count, {
                "total_debits": total_debits,
                "total_credits": total_credits,
                "net_inflow": total_credits - total_debits
            }
        finally:
            db.close()

    @staticmethod
    def verify_ledger_integrity() -> Dict[str, Any]:
        """
        Runs complete consistency validation across all posted journals in the database.
        Checks:
        1. sum(all DEBITs) == sum(all CREDITs)
        2. Per-transaction balance invariant: transaction debits == transaction credits
        """
        db = SessionLocal()
        try:
            all_entries = db.query(LedgerEntry).all()
            total_debits = sum(e.amount_paise for e in all_entries if e.entry_type == "DEBIT")
            total_credits = sum(e.amount_paise for e in all_entries if e.entry_type == "CREDIT")

            # Check per-transaction balancing
            tx_map: Dict[int, Dict[str, int]] = {}
            for e in all_entries:
                if e.transaction_id not in tx_map:
                    tx_map[e.transaction_id] = {"DEBIT": 0, "CREDIT": 0}
                tx_map[e.transaction_id][e.entry_type] += e.amount_paise

            unbalanced_tx_ids = [
                tx_id for tx_id, amounts in tx_map.items()
                if amounts["DEBIT"] != amounts["CREDIT"]
            ]

            return {
                "total_entries": len(all_entries),
                "total_debits_paise": total_debits,
                "total_credits_paise": total_credits,
                "is_system_balanced": total_debits == total_credits,
                "unbalanced_transaction_count": len(unbalanced_tx_ids),
                "unbalanced_transaction_ids": unbalanced_tx_ids
            }
        finally:
            db.close()

    @staticmethod
    def process_credit_card_bill_payment(
        bank_account_id: int,
        credit_card_account_id: int,
        payment_amount_paise: int,
        payment_date: date,
        reference_no: Optional[str] = None
    ) -> Tuple[bool, str, Optional[FinancialTransaction]]:
        """
        Rule 2: A credit card purchase is an expense. Paying the credit card bill
        must reduce CC liability and bank asset WITHOUT creating an expense.
        Journal:
        - DEBIT: Credit Card Liability Account (liability decreases)
        - CREDIT: Bank Account (asset decreases)
        """
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized", None

        if payment_amount_paise <= 0:
            return False, "Payment amount must be greater than zero", None

        current_user = AuthService.get_current_user()
        creator_id = current_user.id if current_user else 1

        db = SessionLocal()
        try:
            bank = db.query(Account).filter_by(id=bank_account_id).first()
            cc = db.query(Account).filter_by(id=credit_card_account_id).first()

            if not bank or not cc or bank.account_type == AccountType.CREDIT_CARD.value or cc.account_type != AccountType.CREDIT_CARD.value:
                return False, "Invalid bank or credit card account selection", None

            txn = FinancialTransaction(
                transaction_type=TransactionType.CREDIT_PAYMENT.value,
                expense_kind="Credit Card Settlement",
                title=f"Bill Payment: {cc.name}",
                description=reference_no or "Monthly Credit Card Bill Clearance",
                amount_paise=payment_amount_paise,
                transaction_date=payment_date,
                account_id=bank_account_id,
                payment_method="Bank Transfer / Auto-Debit",
                reference_no=reference_no,
                created_by_user_id=creator_id,
                paid_by_member_id=1,
                expense_for_member_id=1
            )
            db.add(txn)
            db.flush()

            # Balanced Double-Entry Postings:
            # 1. CREDIT Bank Account (Asset decreases)
            credit_entry = LedgerEntry(
                transaction_id=txn.id,
                account_id=bank_account_id,
                entry_type="CREDIT",
                amount_paise=payment_amount_paise,
                entry_date=payment_date,
                description=f"CC Settlement OUT from {bank.name}"
            )
            db.add(credit_entry)

            # 2. DEBIT Credit Card Account (Liability decreases / balance restores)
            debit_entry = LedgerEntry(
                transaction_id=txn.id,
                account_id=credit_card_account_id,
                entry_type="DEBIT",
                amount_paise=payment_amount_paise,
                entry_date=payment_date,
                description=f"CC Bill Settlement IN for {cc.name}"
            )
            db.add(debit_entry)

            # Update Balances
            bank.current_balance_paise -= payment_amount_paise
            cc.current_balance_paise += payment_amount_paise

            # Audit
            log = AuditLog(
                user_id=creator_id,
                action="CC_BILL_PAID",
                entity_name="ACCOUNT",
                entity_id=cc.id,
                details=f"Settled ₹{payment_amount_paise/100:.2f} CC bill from {bank.name}"
            )
            db.add(log)

            db.commit()
            db.refresh(txn)
            db.expunge(txn)
            return True, "Credit card bill payment processed successfully", txn
        except Exception as e:
            db.rollback()
            return False, str(e), None
        finally:
            db.close()

    @staticmethod
    def get_audit_trail(limit: int = 100) -> List[AuditLog]:
        db = SessionLocal()
        try:
            logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
            for l in logs:
                db.expunge(l)
            return logs
        finally:
            db.close()
