"""
Savings Goals & Contributions Service:
Manages family and individual savings goals, tracks periodic contributions,
computes completion milestones, and coordinates double-entry account deductions.
"""
from typing import List, Optional, Tuple, Dict
from datetime import date
from database.connection import SessionLocal
from database.models import SavingsGoal, SavingsContribution, Account, FamilyMember, AuditLog
from core.authentication import AuthService
from config.constants import GoalPriority

class SavingsService:
    @staticmethod
    def create_goal(
        family_member_id: int,
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

        goal_name = goal_name.strip()
        if not goal_name:
            return False, "Goal name cannot be empty", None

        if target_amount_paise <= 0:
            return False, "Target savings amount must be positive", None

        if target_date < start_date:
            return False, "Target date cannot be earlier than start date", None

        db = SessionLocal()
        try:
            # Validate member
            member = db.query(FamilyMember).filter_by(id=family_member_id).first()
            if not member:
                return False, "Invalid family member selected", None

            goal = SavingsGoal(
                family_member_id=family_member_id,
                goal_name=goal_name,
                target_amount_paise=target_amount_paise,
                current_amount_paise=0,
                start_date=start_date,
                target_date=target_date,
                monthly_contribution_paise=monthly_contribution_paise,
                priority=priority,
                is_completed=False,
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

            # If an account is selected, deduct from account (saved aside into goal)
            if account_id:
                acc = db.query(Account).filter_by(id=account_id).first()
                if not acc:
                    return False, "Selected account not found"
                acc.current_balance_paise -= amount_paise

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

            db.commit()
            return True, "Savings contribution recorded successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    @staticmethod
    def delete_goal(goal_id: int) -> Tuple[bool, str]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized"

        db = SessionLocal()
        try:
            goal = db.query(SavingsGoal).filter_by(id=goal_id).first()
            if not goal:
                return False, "Goal not found"
            db.delete(goal)
            db.commit()
            return True, "Savings goal deleted successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    @staticmethod
    def get_all_goals(family_member_id: Optional[int] = None) -> List[SavingsGoal]:
        db = SessionLocal()
        try:
            query = db.query(SavingsGoal)
            if family_member_id is not None:
                query = query.filter_by(family_member_id=family_member_id)
            results = query.order_by(SavingsGoal.is_completed, SavingsGoal.target_date).all()
            for g in results:
                if g.family_member:
                    _ = g.family_member.name
                _ = g.contributions
                db.expunge(g)
            return results
        finally:
            db.close()

    @staticmethod
    def get_savings_summary(family_member_id: Optional[int] = None) -> Dict:
        goals = SavingsService.get_all_goals(family_member_id)
        total_target = sum(g.target_amount_paise for g in goals)
        total_current = sum(g.current_amount_paise for g in goals)
        completed_count = sum(1 for g in goals if g.is_completed)
        progress_pct = (total_current / total_target * 100) if total_target > 0 else 0

        return {
            "total_target_paise": total_target,
            "total_saved_paise": total_current,
            "remaining_paise": max(0, total_target - total_current),
            "progress_pct": round(progress_pct, 1),
            "total_goals_count": len(goals),
            "completed_goals_count": completed_count,
            "active_goals_count": len(goals) - completed_count
        }
