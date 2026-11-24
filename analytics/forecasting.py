"""
Financial Planning, Forecasting & Cash Runway Engine:
Projects savings, inflation-adjusted expenses, multi-year net worth,
liquid buffer runway, and 12-month future cashflows.
"""
from typing import Dict, Any, List, Optional
from datetime import date, timedelta
import calendar
from database.connection import SessionLocal
from database.models import (
    FinancialTransaction, Account, RecurringRule, Loan, SavingsGoal
)
from config.constants import AccountType, TransactionType, LoanStatus

class ForecastingEngine:
    @staticmethod
    def get_cash_runway() -> Dict[str, Any]:
        """
        Calculates how many months family liquid reserves can sustain current monthly burn rate
        without any additional income.
        """
        db = SessionLocal()
        try:
            # 1. Liquid Accounts (Cash + Savings + Current)
            liquid_accs = db.query(Account).filter(
                Account.is_active == True,
                Account.account_type.in_([
                    AccountType.CASH.value,
                    AccountType.SAVINGS.value,
                    AccountType.CURRENT.value
                ])
            ).all()
            total_liquid_paise = sum(a.current_balance_paise for a in liquid_accs)

            # 2. Monthly Fixed Obligations: Active Loan EMIs
            active_loans = db.query(Loan).filter_by(status=LoanStatus.ACTIVE.value).all()
            monthly_emi_paise = sum(l.emi_amount_paise for l in active_loans)

            # 3. Active Recurring Expenses
            recurring_rules = db.query(RecurringRule).filter(
                RecurringRule.is_active == True,
                RecurringRule.transaction_type == TransactionType.EXPENSE.value
            ).all()
            monthly_recurring_paise = 0
            for r in recurring_rules:
                if r.frequency == "Daily":
                    monthly_recurring_paise += r.amount_paise * 30
                elif r.frequency == "Weekly":
                    monthly_recurring_paise += r.amount_paise * 4
                elif r.frequency == "Monthly":
                    monthly_recurring_paise += r.amount_paise
                elif r.frequency == "Quarterly":
                    monthly_recurring_paise += r.amount_paise // 3
                elif r.frequency == "Yearly":
                    monthly_recurring_paise += r.amount_paise // 12

            # 4. Historical Average Variable Expenses (last 90 days)
            ninety_days_ago = date.today() - timedelta(days=90)
            recent_expenses = db.query(FinancialTransaction).filter(
                FinancialTransaction.is_deleted == False,
                FinancialTransaction.transaction_type == TransactionType.EXPENSE.value,
                FinancialTransaction.transaction_date >= ninety_days_ago
            ).all()

            if recent_expenses:
                total_90d_paise = sum(t.amount_paise for t in recent_expenses)
                monthly_variable_paise = total_90d_paise // 3
            else:
                # Fallback to sum of monthly fixed obligations if no transactions yet
                monthly_variable_paise = 3000000 # Default ₹30,000 baseline

            total_monthly_burn_paise = monthly_emi_paise + monthly_recurring_paise + monthly_variable_paise

            if total_monthly_burn_paise > 0:
                runway_months = round(total_liquid_paise / total_monthly_burn_paise, 1)
            else:
                runway_months = 99.0

            # Health classification
            if runway_months < 3.0:
                health_status = "Critical (Under 3 Months)"
                health_color = "#f43f5e" # Rose/Red
            elif runway_months < 6.0:
                health_status = "Vulnerable (3 - 6 Months)"
                health_color = "#f59e0b" # Amber
            elif runway_months < 12.0:
                health_status = "Moderate (6 - 12 Months)"
                health_color = "#06b6d4" # Cyan
            else:
                health_status = "Healthy Fortress (12+ Months)"
                health_color = "#10b981" # Emerald

            return {
                "total_liquid_paise": total_liquid_paise,
                "monthly_emi_paise": monthly_emi_paise,
                "monthly_recurring_paise": monthly_recurring_paise,
                "monthly_variable_paise": monthly_variable_paise,
                "total_monthly_burn_paise": total_monthly_burn_paise,
                "runway_months": runway_months,
                "health_status": health_status,
                "health_color": health_color
            }
        finally:
            db.close()

    @staticmethod
    def project_12_month_cashflow(
        annual_inflation_pct: float = 6.0,
        expected_income_growth_pct: float = 8.0,
        custom_monthly_income_paise: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generates a 12-month forward simulation of monthly cash inflow, obligations,
        living expenses, net surplus, and cumulative bank balance trajectory.
        """
        runway_info = ForecastingEngine.get_cash_runway()
        starting_cash_paise = runway_info["total_liquid_paise"]
        monthly_emi_paise = runway_info["monthly_emi_paise"]
        monthly_recurring_paise = runway_info["monthly_recurring_paise"]
        base_variable_paise = runway_info["monthly_variable_paise"]

        db = SessionLocal()
        try:
            # Estimate monthly baseline income from last 90 days if not custom provided
            if custom_monthly_income_paise is not None and custom_monthly_income_paise > 0:
                base_income_paise = custom_monthly_income_paise
            else:
                ninety_days_ago = date.today() - timedelta(days=90)
                income_txns = db.query(FinancialTransaction).filter(
                    FinancialTransaction.is_deleted == False,
                    FinancialTransaction.transaction_type == TransactionType.INCOME.value,
                    FinancialTransaction.transaction_date >= ninety_days_ago
                ).all()
                if income_txns:
                    base_income_paise = sum(t.amount_paise for t in income_txns) // 3
                else:
                    base_income_paise = int(round(runway_info["total_monthly_burn_paise"] * 1.3))
        finally:
            db.close()

        monthly_projections = []
        running_bank_balance_paise = starting_cash_paise
        today = date.today()

        monthly_inflation_factor = (1.0 + (annual_inflation_pct / 100.0)) ** (1.0 / 12.0)
        monthly_growth_factor = (1.0 + (expected_income_growth_pct / 100.0)) ** (1.0 / 12.0)

        for m_idx in range(1, 13):
            # Advance month
            target_year = today.year + (today.month + m_idx - 1) // 12
            target_month = (today.month + m_idx - 1) % 12 + 1
            month_label = f"{calendar.month_abbr[target_month]} {target_year}"

            proj_income = int(round(base_income_paise * (monthly_growth_factor ** m_idx)))
            proj_variable = int(round(base_variable_paise * (monthly_inflation_factor ** m_idx)))
            proj_fixed = monthly_emi_paise + monthly_recurring_paise
            total_proj_expenses = proj_fixed + proj_variable

            net_savings = proj_income - total_proj_expenses
            running_bank_balance_paise += net_savings

            monthly_projections.append({
                "month_index": m_idx,
                "month_label": month_label,
                "projected_income_paise": proj_income,
                "fixed_obligations_paise": proj_fixed,
                "variable_expenses_paise": proj_variable,
                "total_expenses_paise": total_proj_expenses,
                "net_savings_paise": net_savings,
                "cumulative_balance_paise": running_bank_balance_paise,
                "savings_rate_pct": round((net_savings / proj_income * 100), 1) if proj_income > 0 else 0
            })

        total_projected_savings = sum(p["net_savings_paise"] for p in monthly_projections)

        return {
            "starting_cash_paise": starting_cash_paise,
            "assumed_monthly_income_paise": base_income_paise,
            "assumed_inflation_pct": annual_inflation_pct,
            "assumed_growth_pct": expected_income_growth_pct,
            "monthly_projections": monthly_projections,
            "total_12m_savings_paise": total_projected_savings,
            "final_projected_cash_paise": running_bank_balance_paise
        }

    @staticmethod
    def project_finances(
        monthly_income_paise: int,
        monthly_expenses_paise: int,
        annual_inflation_pct: float = 6.0,
        expected_income_growth_pct: float = 8.0
    ) -> Dict[str, Any]:
        """
        Projects future savings and expenses across 3m, 6m, 1y, 3y, and 5y horizons.
        """
        horizons = [
            ("3 Months", 0.25),
            ("6 Months", 0.5),
            ("1 Year", 1.0),
            ("3 Years", 3.0),
            ("5 Years", 5.0),
        ]

        monthly_savings_paise = max(0, monthly_income_paise - monthly_expenses_paise)
        projections = []

        current_annual_income = monthly_income_paise * 12
        current_annual_expense = monthly_expenses_paise * 12

        for label, years in horizons:
            growth_mult = (1.0 + (expected_income_growth_pct / 100.0)) ** years
            inflation_mult = (1.0 + (annual_inflation_pct / 100.0)) ** years

            proj_annual_income = int(round(current_annual_income * growth_mult))
            proj_annual_expense = int(round(current_annual_expense * inflation_mult))
            proj_annual_savings = max(0, proj_annual_income - proj_annual_expense)
            period_savings = int(round(proj_annual_savings * years))

            projections.append({
                "horizon": label,
                "projected_expenses_paise": int(round(proj_annual_expense * years)),
                "projected_savings_paise": period_savings,
                "monthly_savings_rate_pct": round((monthly_savings_paise / monthly_income_paise * 100), 1) if monthly_income_paise > 0 else 0
            })

        return {
            "current_monthly_income_paise": monthly_income_paise,
            "current_monthly_expenses_paise": monthly_expenses_paise,
            "current_monthly_savings_paise": monthly_savings_paise,
            "projections": projections,
            "disclaimer": "Projections are mathematical estimates based on stated assumptions and not guaranteed returns."
        }
