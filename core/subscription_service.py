"""
Subscription & Recurring Payments Tracker:
Tracks OTT (Netflix, Prime), broadband, mobile, insurance, software, club memberships.
Computes monthly and annual burn rate, next renewal dates, and optimization flags.
"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import date, timedelta
from database.connection import SessionLocal
from database.models import RecurringRule, Category, Account
from config.constants import TransactionType, RecurringFrequency
from core.authentication import AuthService

class SubscriptionService:
    @staticmethod
    def get_all_subscriptions() -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            rules = db.query(RecurringRule).filter_by(is_active=True).all()
            res = []
            for r in rules:
                # Calculate annual cost equivalent
                mult = 12
                if r.frequency == RecurringFrequency.YEARLY.value:
                    mult = 1
                elif r.frequency == RecurringFrequency.QUARTERLY.value:
                    mult = 4
                elif r.frequency == RecurringFrequency.DAILY.value:
                    mult = 365
                elif r.frequency == RecurringFrequency.WEEKLY.value:
                    mult = 52

                annual_paise = r.amount_paise * mult
                monthly_paise = annual_paise // 12

                res.append({
                    "id": r.id,
                    "title": r.title,
                    "frequency": r.frequency,
                    "amount_paise": r.amount_paise,
                    "monthly_paise": monthly_paise,
                    "annual_paise": annual_paise,
                    "next_due_date": r.next_due_date,
                    "days_until_renewal": (r.next_due_date - date.today()).days,
                    "is_active": r.is_active
                })
            return sorted(res, key=lambda x: x["annual_paise"], reverse=True)
        finally:
            db.close()

    @staticmethod
    def add_subscription(
        title: str,
        amount_paise: int,
        frequency: str,
        start_date: date,
        next_due_date: date,
        account_id: int,
        paid_by_id: int,
        category_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized"

        title = title.strip()
        if not title or amount_paise <= 0:
            return False, "Title and positive amount required"

        db = SessionLocal()
        try:
            from database.models import FamilyMember
            member = db.query(FamilyMember).filter_by(id=paid_by_id).first()
            if not member:
                member = db.query(FamilyMember).filter_by(user_id=paid_by_id).first()
            if not member:
                member = db.query(FamilyMember).first()
            member_id = member.id if member else 1

            rule = RecurringRule(
                title=title,
                transaction_type=TransactionType.EXPENSE.value,
                amount_paise=amount_paise,
                frequency=frequency,
                start_date=start_date,
                next_due_date=next_due_date,
                account_id=account_id,
                paid_by_member_id=member_id,
                category_id=category_id,
                is_active=True
            )
            db.add(rule)
            db.commit()
            return True, "Subscription added successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()
