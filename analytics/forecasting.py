"""
Financial Forecasting & Projection Engine:
Projects savings, inflation-adjusted expenses, and net worth for 3m, 6m, 1y, 3y, and 5y horizons.
"""
from typing import Dict, Any, List
from datetime import date
from analytics.expense_analysis import AnalyticsService

class ForecastingEngine:
    @staticmethod
    def project_finances(
        monthly_income_paise: int,
        monthly_expenses_paise: int,
        annual_inflation_pct: float = 6.0,
        expected_income_growth_pct: float = 8.0
    ) -> Dict[str, Any]:
        """
        Projects future savings and expenses across multiple horizons.
        Clearly labeled as mathematical estimates.
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

        cumulative_savings = 0
        current_annual_income = monthly_income_paise * 12
        current_annual_expense = monthly_expenses_paise * 12

        for label, years in horizons:
            # Compound growth
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
