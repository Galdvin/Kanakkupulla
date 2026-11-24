"""
Savings Goals & Contributions Service
"""
from typing import List, Optional, Tuple
from datetime import date
from database.connection import SessionLocal
from database.models import SavingsGoal, SavingsContribution, Account, AuditLog
from core.authentication import AuthService
from config.constants import GoalPriority

class SavingsService:
    @staticmethod
    def create_goal(
        user_id: int,
        goal_name: str,
        target_amount_paise: int,
        start_date: date,
        target_date: date,
        monthly_contribution_paise: int = 0,
        priority: str = GoalPriority.MEDIUM.value,
        notes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[SavingsGoal]]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized", None

        if target_amount_paise <= 0:
            return False, "Target savings amount must be positive", None

        db = SessionLocal()
        try:
            goal = SavingsGoal(
                user_id=user_id,
                goal_name=goal_name.strip(),
                target_amount_paise=target_amount_paise,
                current_amount_paise=0,
                start_date=start_date,
                target_date=target_date,
                monthly_contribution_paise=monthly_contribution_paise,
                priority=priority,
                notes=notes
            )
            db.add(goal)
            db.commit()
            db.refresh(goal)
            db.expunge(goal)
            return True, "Savings goal created successfully", goal
        except Exception as e:
            db.rollback()
            return False, str(e), None
        finally:
            db.close()

    @staticmethod
    def record_contribution(
        goal_id: int,
        amount_paise: int,
        contribution_date: date,
        account_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, str]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized"

        if amount_paise <= 0:
            return False, "Contribution amount must be positive"

        db = SessionLocal()
        try:
            goal = db.query(SavingsGoal).filter_by(id=goal_id).first()
            if not goal:
                return False, "Savings goal not found"

            contrib = SavingsContribution(
                goal_id=goal_id,
                account_id=account_id,
                amount_paise=amount_paise,
                contribution_date=contribution_date,
                notes=notes
            )
            db.add(contrib)

            # Update goal accumulated amount
            goal.current_amount_paise += amount_paise
            if goal.current_amount_paise >= goal.target_amount_paise:
                goal.is_completed = True

            # If an account is selected, deduct from account (saved aside)
            if account_id:
                acc = db.query(Account).filter_by(id=account_id).first()
                if acc:
                    acc.current_balance_paise -= amount_paise

            db.commit()
            return True, "Savings contribution recorded successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    @staticmethod
    def get_all_goals() -> List[SavingsGoal]:
        db = SessionLocal()
        try:
            results = db.query(SavingsGoal).order_by(SavingsGoal.target_date).all()
            for g in results:
                _ = g.user.full_name if g.user else None
                db.expunge(g)
            return results
        finally:
            db.close()
