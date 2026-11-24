"""
Analytics Service for Family & Individual Financial Intelligence:
Calculates:
- Consolidated Family Finances vs Individual Member Financial Position
- 8 Master KPI Cards:
  1. Total Family Income
  2. Total Family Expenses
  3. Total Family Savings
  4. Available Bank Balance
  5. Monthly Budget Remaining
  6. Total Investments
  7. Total Liabilities
  8. Family Net Worth
- Payer-wise vs Beneficiary-wise breakdowns
"""
from typing import Dict, Any, List, Optional
from datetime import date
from database.connection import SessionLocal
from database.models import (
    FinancialTransaction, Account, Budget, Investment, Loan, FamilyMember
)
from config.constants import TransactionType, LoanStatus, AccountType

class AnalyticsService:
    @staticmethod
    def get_dashboard_metrics(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        filter_member_id: Optional[int] = None # None = Consolidated Family, or specific member
    ) -> Dict[str, Any]:
        if not start_date:
            today = date.today()
            start_date = date(today.year, today.month, 1)
        if not end_date:
            end_date = date.today()

        db = SessionLocal()
        try:
            # 1. Incomes
            q_inc = db.query(FinancialTransaction).filter(
                FinancialTransaction.transaction_type == TransactionType.INCOME.value,
                FinancialTransaction.is_deleted == False,
                FinancialTransaction.transaction_date >= start_date,
                FinancialTransaction.transaction_date <= end_date
            )
            if filter_member_id:
                q_inc = q_inc.filter(FinancialTransaction.paid_by_member_id == filter_member_id)
            incomes = q_inc.all()
            total_income_paise = sum(t.amount_paise for t in incomes)

            # 2. Expenses (Net of Reversals)
            q_exp = db.query(FinancialTransaction).filter(
                FinancialTransaction.transaction_type == TransactionType.EXPENSE.value,
                FinancialTransaction.is_deleted == False,
                FinancialTransaction.transaction_date >= start_date,
                FinancialTransaction.transaction_date <= end_date
            )
            if filter_member_id:
                # Filter by payer or beneficiary depending on context
                q_exp = q_exp.filter(FinancialTransaction.paid_by_member_id == filter_member_id)
            expenses = q_exp.all()
            total_expense_paise = sum(t.amount_paise for t in expenses)

            # 3. Savings
            total_savings_paise = total_income_paise - total_expense_paise
            savings_rate_pct = (total_savings_paise / total_income_paise * 100) if total_income_paise > 0 else 0

            # 4. Bank Balance
            accounts = db.query(Account).filter_by(is_active=True).all()
            liquid_balance_paise = sum(a.current_balance_paise for a in accounts if a.account_type != AccountType.CREDIT_CARD.value)

            # 5. Monthly Budget
            budgets = db.query(Budget).filter(
                Budget.start_date <= end_date,
                Budget.end_date >= start_date
            ).all()
            total_budget_paise = sum(b.total_budget_paise for b in budgets)
            budget_remaining_paise = max(0, total_budget_paise - total_expense_paise)
            budget_utilization_pct = (total_expense_paise / total_budget_paise * 100) if total_budget_paise > 0 else 0

            # 6. Investments
            q_inv = db.query(Investment)
            if filter_member_id:
                q_inv = q_inv.filter(Investment.family_member_id == filter_member_id)
            investments = q_inv.all()
            total_investments_paise = sum(i.current_value_paise for i in investments)

            # 7. Liabilities (Loans + Credit Card debt)
            q_loans = db.query(Loan).filter_by(status=LoanStatus.ACTIVE.value)
            if filter_member_id:
                q_loans = q_loans.filter(Loan.family_member_id == filter_member_id)
            loans = q_loans.all()
            loans_liabilities = sum(l.outstanding_principal_paise for l in loans)
            cc_liabilities = sum(abs(a.current_balance_paise) for a in accounts if a.account_type == AccountType.CREDIT_CARD.value and a.current_balance_paise < 0)
            total_liabilities_paise = loans_liabilities + cc_liabilities

            # 8. Net Worth = Assets - Liabilities
            total_assets_paise = liquid_balance_paise + total_investments_paise
            family_net_worth_paise = total_assets_paise - total_liabilities_paise

            # Category Distribution
            cat_map: Dict[str, int] = {}
            for e in expenses:
                cname = e.category.name if e.category else "Uncategorized"
                cat_map[cname] = cat_map.get(cname, 0) + e.amount_paise

            category_distribution = sorted(
                [{"name": k, "amount_paise": v} for k, v in cat_map.items()],
                key=lambda x: x["amount_paise"],
                reverse=True
            )

            # Payer vs Beneficiary Distribution
            payer_map: Dict[str, int] = {}
            beneficiary_map: Dict[str, int] = {}
            for e in expenses:
                pname = e.paid_by_member.name if e.paid_by_member else "Unknown"
                bname = e.expense_for_member.name if e.expense_for_member else "Unknown"
                payer_map[pname] = payer_map.get(pname, 0) + e.amount_paise
                beneficiary_map[bname] = beneficiary_map.get(bname, 0) + e.amount_paise

            return {
                "total_income_paise": total_income_paise,
                "total_expense_paise": total_expense_paise,
                "total_savings_paise": total_savings_paise,
                "savings_rate_pct": round(savings_rate_pct, 1),
                "liquid_balance_paise": liquid_balance_paise,
                "total_budget_paise": total_budget_paise,
                "budget_remaining_paise": budget_remaining_paise,
                "budget_utilization_pct": round(budget_utilization_pct, 1),
                "total_investments_paise": total_investments_paise,
                "total_liabilities_paise": total_liabilities_paise,
                "family_net_worth_paise": family_net_worth_paise,
                "category_distribution": category_distribution,
                "user_distribution": [{"user": k, "amount_paise": v} for k, v in payer_map.items()],
                "beneficiary_distribution": [{"beneficiary": k, "amount_paise": v} for k, v in beneficiary_map.items()]
            }
        finally:
            db.close()
