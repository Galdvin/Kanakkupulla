"""
Financial Calendar Service:
Aggregates daily spending, income, scheduled bill dates, and loan EMI events for interactive calendar views.
"""
from typing import Dict, List, Optional
from datetime import date
import calendar
from database.connection import SessionLocal
from database.models import (
    FinancialTransaction, RecurringRule, Loan, Account
)
from config.constants import TransactionType, LoanStatus

class CalendarService:
    @staticmethod
    def get_month_calendar_data(year: int, month: int) -> Dict:
        """
        Retrieves day-by-day actual transactions and scheduled events (recurring bills + loan EMIs)
        for the given year and month.
        """
        _, num_days = calendar.monthrange(year, month)
        first_day_of_month = date(year, month, 1)
        last_day_of_month = date(year, month, num_days)

        db = SessionLocal()
        try:
            # 1. Actual transactions in this month
            actual_txns = db.query(FinancialTransaction).filter(
                FinancialTransaction.is_deleted == False,
                FinancialTransaction.transaction_date >= first_day_of_month,
                FinancialTransaction.transaction_date <= last_day_of_month
            ).all()

            # 2. Active Recurring Rules
            recurring_rules = db.query(RecurringRule).filter(
                RecurringRule.is_active == True
            ).all()

            # 3. Active Loans (EMI due days)
            active_loans = db.query(Loan).filter(
                Loan.status == LoanStatus.ACTIVE.value
            ).all()

            # Initialize daily buckets
            daily_data: Dict[int, Dict] = {}
            for day in range(1, num_days + 1):
                daily_data[day] = {
                    "day": day,
                    "date": date(year, month, day),
                    "day_name": calendar.day_abbr[date(year, month, day).weekday()],
                    "actual_expense_paise": 0,
                    "actual_income_paise": 0,
                    "scheduled_expense_paise": 0,
                    "scheduled_income_paise": 0,
                    "transactions": [],
                    "scheduled_events": []
                }

            # Map actual transactions to days
            total_actual_expense = 0
            total_actual_income = 0

            for txn in actual_txns:
                day_num = txn.transaction_date.day
                bucket = daily_data[day_num]
                
                cat_name = txn.category.name if txn.category else "General"
                member_name = txn.paid_by_member.name if txn.paid_by_member else "Family"

                t_info = {
                    "id": txn.id,
                    "title": txn.title,
                    "type": txn.transaction_type,
                    "amount_paise": txn.amount_paise,
                    "category": cat_name,
                    "paid_by": member_name,
                    "time": txn.transaction_time
                }
                bucket["transactions"].append(t_info)

                if txn.transaction_type == TransactionType.EXPENSE.value:
                    bucket["actual_expense_paise"] += txn.amount_paise
                    total_actual_expense += txn.amount_paise
                elif txn.transaction_type == TransactionType.INCOME.value:
                    bucket["actual_income_paise"] += txn.amount_paise
                    total_actual_income += txn.amount_paise

            # Map Loan EMI events
            total_scheduled_expense = 0
            for loan in active_loans:
                due_day = min(loan.emi_due_day, num_days)
                bucket = daily_data[due_day]
                bucket["scheduled_events"].append({
                    "kind": "Loan EMI",
                    "title": f"EMI: {loan.loan_name} ({loan.lender})",
                    "amount_paise": loan.emi_amount_paise,
                    "type": TransactionType.EXPENSE.value
                })
                bucket["scheduled_expense_paise"] += loan.emi_amount_paise
                total_scheduled_expense += loan.emi_amount_paise

            # Map Recurring Rules
            for rule in recurring_rules:
                curr_date = rule.next_due_date
                # Advance backwards or forwards to check if falls in this month
                # For monthly/quarterly/yearly, check if rule matches current month
                due_day = min(rule.start_date.day, num_days)
                # If start_date <= last_day_of_month and (end_date is None or end_date >= first_day_of_month)
                if rule.start_date <= last_day_of_month and (not rule.end_date or rule.end_date >= first_day_of_month):
                    # Check if due in this month
                    if rule.frequency == "Monthly" or rule.frequency == "Daily":
                        bucket = daily_data[due_day]
                        bucket["scheduled_events"].append({
                            "kind": "Recurring Rule",
                            "title": rule.title,
                            "amount_paise": rule.amount_paise,
                            "type": rule.transaction_type
                        })
                        if rule.transaction_type == TransactionType.EXPENSE.value:
                            bucket["scheduled_expense_paise"] += rule.amount_paise
                            total_scheduled_expense += rule.amount_paise

            max_spend = max((b["actual_expense_paise"] for b in daily_data.values()), default=0)

            return {
                "year": year,
                "month": month,
                "month_name": calendar.month_name[month],
                "num_days": num_days,
                "first_weekday": first_day_of_month.weekday(), # 0 = Monday, 6 = Sunday
                "daily_data": daily_data,
                "total_actual_expense_paise": total_actual_expense,
                "total_actual_income_paise": total_actual_income,
                "total_scheduled_expense_paise": total_scheduled_expense,
                "net_cashflow_paise": total_actual_income - total_actual_expense,
                "max_daily_spend_paise": max_spend
            }
        finally:
            db.close()
