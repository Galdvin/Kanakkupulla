"""
Recurring Transactions & Automated Rules Service:
Schedules and processes recurring expenses (rent, utilities, insurance, subscriptions, EMIs)
and recurring incomes (salary, dividends, rental income) with balanced double-entry accounting.
"""
from typing import List, Optional, Tuple, Dict
from datetime import date, timedelta
import calendar
from database.connection import SessionLocal
from database.models import (
    RecurringRule, FinancialTransaction, Account, Category,
    FamilyMember, User, LedgerEntry
)
from core.authentication import AuthService
from config.constants import TransactionType, RecurringFrequency

class RecurringService:
    @staticmethod
    def advance_date(curr_date: date, frequency: str) -> date:
        """Calculates next due date based on recurrence frequency."""
        freq = frequency.capitalize()
        if freq == "Daily":
            return curr_date + timedelta(days=1)
        elif freq == "Weekly":
            return curr_date + timedelta(days=7)
        elif freq == "Monthly":
            # Advance by 1 month preserving day
            year = curr_date.year + (1 if curr_date.month == 12 else 0)
            month = 1 if curr_date.month == 12 else curr_date.month + 1
            _, max_day = calendar.monthrange(year, month)
            day = min(curr_date.day, max_day)
            return date(year, month, day)
        elif freq == "Quarterly":
            # Advance by 3 months
            new_month = curr_date.month + 3
            year = curr_date.year + (new_month - 1) // 12
            month = (new_month - 1) % 12 + 1
            _, max_day = calendar.monthrange(year, month)
            day = min(curr_date.day, max_day)
            return date(year, month, day)
        elif freq == "Yearly" or freq == "Annual":
            try:
                return curr_date.replace(year=curr_date.year + 1)
            except ValueError:
                # Handle Feb 29 leap year
                return curr_date.replace(year=curr_date.year + 1, day=28)
        else:
            return curr_date + timedelta(days=30)

    @staticmethod
    def create_rule(
        title: str,
        transaction_type: str,
        amount_paise: int,
        frequency: str,
        start_date: date,
        account_id: int,
        paid_by_member_id: int,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        end_date: Optional[date] = None
    ) -> Tuple[bool, str, Optional[RecurringRule]]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized", None

        title = title.strip()
        if not title:
            return False, "Rule title is required", None

        if amount_paise <= 0:
            return False, "Amount must be positive", None

        if end_date and end_date < start_date:
            return False, "End date cannot be earlier than start date", None

        db = SessionLocal()
        try:
            acc = db.query(Account).filter_by(id=account_id).first()
            if not acc:
                return False, "Invalid account selected", None

            member = db.query(FamilyMember).filter_by(id=paid_by_member_id).first()
            if not member:
                return False, "Invalid family member selected", None

            rule = RecurringRule(
                title=title,
                transaction_type=transaction_type,
                amount_paise=amount_paise,
                frequency=frequency.capitalize(),
                start_date=start_date,
                end_date=end_date,
                next_due_date=start_date,
                account_id=account_id,
                paid_by_member_id=paid_by_member_id,
                category_id=category_id,
                subcategory_id=subcategory_id,
                is_active=True
            )
            db.add(rule)
            db.commit()
            db.refresh(rule)
            db.expunge(rule)
            return True, "Recurring rule created successfully", rule
        except Exception as e:
            db.rollback()
            return False, str(e), None
        finally:
            db.close()

    @staticmethod
    def toggle_rule(rule_id: int) -> Tuple[bool, str, bool]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized", False

        db = SessionLocal()
        try:
            rule = db.query(RecurringRule).filter_by(id=rule_id).first()
            if not rule:
                return False, "Rule not found", False
            rule.is_active = not rule.is_active
            new_state = rule.is_active
            db.commit()
            return True, f"Rule {'activated' if new_state else 'paused'}", new_state
        except Exception as e:
            db.rollback()
            return False, str(e), False
        finally:
            db.close()

    @staticmethod
    def delete_rule(rule_id: int) -> Tuple[bool, str]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized"

        db = SessionLocal()
        try:
            rule = db.query(RecurringRule).filter_by(id=rule_id).first()
            if not rule:
                return False, "Rule not found"
            db.delete(rule)
            db.commit()
            return True, "Recurring rule deleted successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    @staticmethod
    def get_all_rules(family_member_id: Optional[int] = None) -> List[RecurringRule]:
        db = SessionLocal()
        try:
            query = db.query(RecurringRule)
            if family_member_id is not None:
                query = query.filter_by(paid_by_member_id=family_member_id)
            rules = query.order_by(RecurringRule.is_active.desc(), RecurringRule.next_due_date).all()
            for r in rules:
                if r.category:
                    _ = r.category.name
                if r.account:
                    _ = r.account.name
                if r.paid_by_member:
                    _ = r.paid_by_member.name
                db.expunge(r)
            return rules
        finally:
            db.close()

    @staticmethod
    def process_due_rules(up_to_date: Optional[date] = None) -> Tuple[int, List[Dict]]:
        """
        Executes active recurring rules that are due up to `up_to_date` (defaults to today).
        Creates FinancialTransaction and double-entry ledger entries. Advances next_due_date.
        """
        if up_to_date is None:
            up_to_date = date.today()

        db = SessionLocal()
        created_records = []
        try:
            due_rules = db.query(RecurringRule).filter(
                RecurringRule.is_active == True,
                RecurringRule.next_due_date <= up_to_date
            ).all()

            current_user = AuthService.get_current_user()
            user_id = current_user.id if current_user else 1

            for rule in due_rules:
                # While next_due_date is <= up_to_date and not past end_date, generate transactions
                while rule.is_active and rule.next_due_date <= up_to_date:
                    if rule.end_date and rule.next_due_date > rule.end_date:
                        rule.is_active = False
                        break

                    # 1. Create FinancialTransaction
                    txn = FinancialTransaction(
                        title=f"{rule.title} (Recurring)",
                        transaction_type=rule.transaction_type,
                        expense_kind="Daily",
                        amount_paise=rule.amount_paise,
                        transaction_date=rule.next_due_date,
                        account_id=rule.account_id,
                        category_id=rule.category_id,
                        subcategory_id=rule.subcategory_id,
                        payment_method="Recurring / Auto Debit",
                        created_by_user_id=user_id,
                        paid_by_member_id=rule.paid_by_member_id,
                        expense_for_member_id=rule.paid_by_member_id,
                        is_recurring=True
                    )
                    db.add(txn)
                    db.flush()

                    # 2. Update Account Balance
                    acc = db.query(Account).filter_by(id=rule.account_id).first()
                    if acc:
                        if rule.transaction_type == TransactionType.EXPENSE.value:
                            acc.current_balance_paise -= rule.amount_paise
                        elif rule.transaction_type == TransactionType.INCOME.value:
                            acc.current_balance_paise += rule.amount_paise

                    # 3. Create double-entry ledger entries
                    if rule.transaction_type == TransactionType.EXPENSE.value:
                        entry1 = LedgerEntry(
                            transaction_id=txn.id,
                            account_id=rule.account_id,
                            entry_type="CREDIT",
                            amount_paise=rule.amount_paise,
                            entry_date=rule.next_due_date,
                            description=f"Paid Recurring: {rule.title}"
                        )
                        entry2 = LedgerEntry(
                            transaction_id=txn.id,
                            account_id=rule.account_id,
                            entry_type="DEBIT",
                            amount_paise=rule.amount_paise,
                            entry_date=rule.next_due_date,
                            description=f"Recurring Expense: {rule.title}"
                        )
                    else:
                        entry1 = LedgerEntry(
                            transaction_id=txn.id,
                            account_id=rule.account_id,
                            entry_type="DEBIT",
                            amount_paise=rule.amount_paise,
                            entry_date=rule.next_due_date,
                            description=f"Received Recurring: {rule.title}"
                        )
                        entry2 = LedgerEntry(
                            transaction_id=txn.id,
                            account_id=rule.account_id,
                            entry_type="CREDIT",
                            amount_paise=rule.amount_paise,
                            entry_date=rule.next_due_date,
                            description=f"Recurring Income: {rule.title}"
                        )
                    db.add_all([entry1, entry2])

                    created_records.append({
                        "rule_id": rule.id,
                        "title": rule.title,
                        "amount_paise": rule.amount_paise,
                        "date": rule.next_due_date,
                        "transaction_id": txn.id
                    })

                    # Advance rule
                    rule.next_due_date = RecurringService.advance_date(rule.next_due_date, rule.frequency)
                    if rule.end_date and rule.next_due_date > rule.end_date:
                        rule.is_active = False

            db.commit()
            return len(created_records), created_records
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    @staticmethod
    def get_upcoming_commitments(days_ahead: int = 30) -> Dict:
        """Returns recurring payments due within next N days and total projected outflow."""
        today = date.today()
        target_date = today + timedelta(days=days_ahead)
        rules = RecurringService.get_all_rules()

        upcoming = []
        total_outflow_paise = 0
        total_inflow_paise = 0

        for r in rules:
            if not r.is_active:
                continue

            curr_due = r.next_due_date
            while curr_due <= target_date:
                if curr_due >= today:
                    item = {
                        "rule_id": r.id,
                        "title": r.title,
                        "type": r.transaction_type,
                        "amount_paise": r.amount_paise,
                        "due_date": curr_due,
                        "frequency": r.frequency,
                        "account_name": r.account.name if r.account else "Account",
                        "member_name": r.paid_by_member.name if r.paid_by_member else "Family"
                    }
                    upcoming.append(item)
                    if r.transaction_type == TransactionType.EXPENSE.value:
                        total_outflow_paise += r.amount_paise
                    else:
                        total_inflow_paise += r.amount_paise

                curr_due = RecurringService.advance_date(curr_due, r.frequency)
                if r.end_date and curr_due > r.end_date:
                    break

        upcoming.sort(key=lambda x: x["due_date"])
        return {
            "upcoming_events": upcoming,
            "total_outflow_paise": total_outflow_paise,
            "total_inflow_paise": total_inflow_paise,
            "net_projected_paise": total_inflow_paise - total_outflow_paise
        }
