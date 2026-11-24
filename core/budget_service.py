"""
Budget Management Service:
Supports Monthly, Quarterly, and Yearly budgets with Category allocations,
spent tracking, remaining amounts, and utilization alert calculations (50%, 75%, 90%, 100%+).
"""
from typing import List, Optional, Tuple, Dict
from datetime import date
from database.connection import SessionLocal
from database.models import Budget, BudgetCategory, Transaction, Category
from config.constants import TransactionType
from core.authentication import AuthService

class BudgetService:
    @staticmethod
    def create_budget(
        name: str,
        period_type: str,
        start_date: date,
        end_date: date,
        total_budget_paise: int,
        category_allocations: Dict[int, int] # category_id -> allocated_paise
    ) -> Tuple[bool, str, Optional[Budget]]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized", None

        name = name.strip()
        if not name:
            return False, "Budget name is required", None

        if total_budget_paise <= 0:
            return False, "Budget amount must be positive", None

        db = SessionLocal()
        try:
            budget = Budget(
                name=name,
                period_type=period_type,
                start_date=start_date,
                end_date=end_date,
                total_budget_paise=total_budget_paise
            )
            db.add(budget)
            db.flush()

            for cat_id, alloc_paise in category_allocations.items():
                if alloc_paise > 0:
                    bc = BudgetCategory(
                        budget_id=budget.id,
                        category_id=cat_id,
                        allocated_paise=alloc_paise
                    )
                    db.add(bc)

            db.commit()
            db.refresh(budget)
            db.expunge(budget)
            return True, "Budget created successfully", budget
        except Exception as e:
            db.rollback()
            return False, str(e), None
        finally:
            db.close()

    @staticmethod
    def get_budget_status(budget_id: int) -> Optional[Dict]:
        """Calculates actual spent vs allocated budget and utilization percentage"""
        db = SessionLocal()
        try:
            budget = db.query(Budget).filter_by(id=budget_id).first()
            if not budget:
                return None

            # Calculate total spent in budget period
            spent_txns = db.query(Transaction).filter(
                Transaction.transaction_type == TransactionType.EXPENSE.value,
                Transaction.is_deleted == False,
                Transaction.transaction_date >= budget.start_date,
                Transaction.transaction_date <= budget.end_date
            ).all()

            total_spent_paise = sum(t.amount_paise for t in spent_txns)
            remaining_paise = budget.total_budget_paise - total_spent_paise
            utilization_pct = (total_spent_paise / budget.total_budget_paise * 100) if budget.total_budget_paise > 0 else 0

            # Category breakdowns
            cat_breakdown = []
            for bc in budget.category_budgets:
                cat_spent = sum(t.amount_paise for t in spent_txns if t.category_id == bc.category_id)
                cat_breakdown.append({
                    "category_id": bc.category_id,
                    "category_name": bc.category.name if bc.category else "Unknown",
                    "allocated_paise": bc.allocated_paise,
                    "spent_paise": cat_spent,
                    "remaining_paise": bc.allocated_paise - cat_spent,
                    "utilization_pct": (cat_spent / bc.allocated_paise * 100) if bc.allocated_paise > 0 else 0
                })

            return {
                "budget_id": budget.id,
                "name": budget.name,
                "total_budget_paise": budget.total_budget_paise,
                "total_spent_paise": total_spent_paise,
                "remaining_paise": remaining_paise,
                "utilization_pct": round(utilization_pct, 1),
                "is_exceeded": total_spent_paise > budget.total_budget_paise,
                "category_breakdown": cat_breakdown
            }
        finally:
            db.close()

    @staticmethod
    def get_all_budgets() -> List[Budget]:
        db = SessionLocal()
        try:
            results = db.query(Budget).order_by(Budget.start_date.desc()).all()
            for b in results:
                db.expunge(b)
            return results
        finally:
            db.close()
