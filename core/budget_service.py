"""
Budget Management Service:
Supports Monthly, Quarterly, and Yearly budgets with Category allocations,
spent tracking against FinancialTransaction, remaining amounts, alert calculations
(Normal <75%, Caution 75-90%, Warning 90-100%, Exceeded >=100%),
and support for both Shared Family Budgets and Individual Member Budgets.
"""
from typing import List, Optional, Tuple, Dict
from datetime import date
from database.connection import SessionLocal
from database.models import Budget, BudgetCategory, FinancialTransaction, Category, FamilyMember
from config.constants import TransactionType
from core.authentication import AuthService

class BudgetAlertLevel:
    NORMAL = "Normal"     # < 75%
    CAUTION = "Caution"   # 75% - 89.9%
    WARNING = "Warning"   # 90% - 99.9%
    EXCEEDED = "Exceeded" # >= 100%

class BudgetService:
    @staticmethod
    def create_budget(
        name: str,
        period_type: str,
        start_date: date,
        end_date: date,
        total_budget_paise: int,
        category_allocations: Dict[int, int], # category_id -> allocated_paise
        family_member_id: Optional[int] = None # None means Entire Family
    ) -> Tuple[bool, str, Optional[Budget]]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized", None

        name = name.strip()
        if not name:
            return False, "Budget name is required", None

        if total_budget_paise <= 0:
            return False, "Budget amount must be positive", None

        if end_date < start_date:
            return False, "End date cannot be earlier than start date", None

        db = SessionLocal()
        try:
            budget = Budget(
                name=name,
                period_type=period_type,
                start_date=start_date,
                end_date=end_date,
                total_budget_paise=total_budget_paise,
                family_member_id=family_member_id
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
    def delete_budget(budget_id: int) -> Tuple[bool, str]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized"

        db = SessionLocal()
        try:
            budget = db.query(Budget).filter_by(id=budget_id).first()
            if not budget:
                return False, "Budget not found"
            db.delete(budget)
            db.commit()
            return True, "Budget deleted successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    @staticmethod
    def get_budget_status(budget_id: int) -> Optional[Dict]:
        """Calculates actual spent vs allocated budget and utilization percentage with alert tiers."""
        db = SessionLocal()
        try:
            budget = db.query(Budget).filter_by(id=budget_id).first()
            if not budget:
                return None

            # Calculate spent transactions in budget period
            query = db.query(FinancialTransaction).filter(
                FinancialTransaction.transaction_type == TransactionType.EXPENSE.value,
                FinancialTransaction.is_deleted == False,
                FinancialTransaction.transaction_date >= budget.start_date,
                FinancialTransaction.transaction_date <= budget.end_date
            )

            # If this is an individual member budget, filter by beneficiary or payer
            if budget.family_member_id is not None:
                query = query.filter(
                    (FinancialTransaction.expense_for_member_id == budget.family_member_id) |
                    (FinancialTransaction.paid_by_member_id == budget.family_member_id)
                )

            spent_txns = query.all()

            total_spent_paise = sum(t.amount_paise for t in spent_txns)
            remaining_paise = budget.total_budget_paise - total_spent_paise
            utilization_pct = (total_spent_paise / budget.total_budget_paise * 100) if budget.total_budget_paise > 0 else 0

            # Determine alert level
            if utilization_pct >= 100.0:
                alert_level = BudgetAlertLevel.EXCEEDED
            elif utilization_pct >= 90.0:
                alert_level = BudgetAlertLevel.WARNING
            elif utilization_pct >= 75.0:
                alert_level = BudgetAlertLevel.CAUTION
            else:
                alert_level = BudgetAlertLevel.NORMAL

            # Category breakdowns
            cat_breakdown = []
            for bc in budget.category_budgets:
                cat_spent = sum(t.amount_paise for t in spent_txns if t.category_id == bc.category_id)
                cat_rem = bc.allocated_paise - cat_spent
                cat_pct = (cat_spent / bc.allocated_paise * 100) if bc.allocated_paise > 0 else 0

                cat_alert = BudgetAlertLevel.NORMAL
                if cat_pct >= 100.0:
                    cat_alert = BudgetAlertLevel.EXCEEDED
                elif cat_pct >= 90.0:
                    cat_alert = BudgetAlertLevel.WARNING
                elif cat_pct >= 75.0:
                    cat_alert = BudgetAlertLevel.CAUTION

                cat_breakdown.append({
                    "category_id": bc.category_id,
                    "category_name": bc.category.name if bc.category else "Unknown",
                    "allocated_paise": bc.allocated_paise,
                    "spent_paise": cat_spent,
                    "remaining_paise": cat_rem,
                    "utilization_pct": round(cat_pct, 1),
                    "alert_level": cat_alert
                })

            member_name = budget.family_member.name if budget.family_member else "Entire Family (Shared)"

            return {
                "budget_id": budget.id,
                "name": budget.name,
                "period_type": budget.period_type,
                "start_date": budget.start_date,
                "end_date": budget.end_date,
                "family_member_id": budget.family_member_id,
                "member_name": member_name,
                "total_budget_paise": budget.total_budget_paise,
                "total_spent_paise": total_spent_paise,
                "remaining_paise": remaining_paise,
                "utilization_pct": round(utilization_pct, 1),
                "alert_level": alert_level,
                "is_exceeded": total_spent_paise > budget.total_budget_paise,
                "category_breakdown": cat_breakdown
            }
        finally:
            db.close()

    @staticmethod
    def get_all_budgets(family_member_id: Optional[int] = None) -> List[Budget]:
        db = SessionLocal()
        try:
            query = db.query(Budget)
            if family_member_id is not None:
                query = query.filter((Budget.family_member_id == family_member_id) | (Budget.family_member_id == None))
            results = query.order_by(Budget.start_date.desc()).all()
            for b in results:
                _ = b.category_budgets
                if b.family_member:
                    _ = b.family_member.name
                db.expunge(b)
            return results
        finally:
            db.close()

    @staticmethod
    def get_overall_budget_summary() -> Dict:
        """Returns aggregate KPI numbers across active budgets"""
        budgets = BudgetService.get_all_budgets()
        total_budgeted = 0
        total_spent = 0

        for b in budgets:
            st = BudgetService.get_budget_status(b.id)
            if st:
                total_budgeted += st["total_budget_paise"]
                total_spent += st["total_spent_paise"]

        util_pct = (total_spent / total_budgeted * 100) if total_budgeted > 0 else 0
        return {
            "total_budget_paise": total_budgeted,
            "total_spent_paise": total_spent,
            "remaining_paise": total_budgeted - total_spent,
            "utilization_pct": round(util_pct, 1),
            "budget_count": len(budgets)
        }
