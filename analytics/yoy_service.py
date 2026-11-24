"""
Year-Over-Year (YoY) Financial Analytics Engine:
Compares annual expenditure, income, savings, and investment accumulation across years.
"""
from typing import Dict, Any, List
from datetime import date
from database.connection import SessionLocal
from database.models import Transaction
from config.constants import TransactionType

class YearOverYearService:
    @staticmethod
    def compare_years(base_year: int, target_year: int) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            def get_year_metrics(year: int):
                start = date(year, 1, 1)
                end = date(year, 12, 31)

                inc = db.query(Transaction).filter(
                    Transaction.transaction_type == TransactionType.INCOME.value,
                    Transaction.is_deleted == False,
                    Transaction.transaction_date >= start,
                    Transaction.transaction_date <= end
                ).all()

                exp = db.query(Transaction).filter(
                    Transaction.transaction_type == TransactionType.EXPENSE.value,
                    Transaction.is_deleted == False,
                    Transaction.transaction_date >= start,
                    Transaction.transaction_date <= end
                ).all()

                total_inc = sum(t.amount_paise for t in inc)
                total_exp = sum(t.amount_paise for t in exp)
                savings = total_inc - total_exp

                return {
                    "income_paise": total_inc,
                    "expense_paise": total_exp,
                    "savings_paise": savings
                }

            base_data = get_year_metrics(base_year)
            target_data = get_year_metrics(target_year)

            # Growth percentages
            def calc_growth(old_val: int, new_val: int) -> float:
                if old_val == 0:
                    return 0.0
                return round(((new_val - old_val) / old_val) * 100, 1)

            return {
                "base_year": base_year,
                "target_year": target_year,
                "base_data": base_data,
                "target_data": target_data,
                "income_growth_pct": calc_growth(base_data["income_paise"], target_data["income_paise"]),
                "expense_growth_pct": calc_growth(base_data["expense_paise"], target_data["expense_paise"]),
                "savings_growth_pct": calc_growth(base_data["savings_paise"], target_data["savings_paise"])
            }
        finally:
            db.close()
