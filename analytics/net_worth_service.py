"""
Net Worth Tracking Service:
Assets = Liquid Bank Balances + Cash + Investments + Fixed Deposits
Liabilities = Active Loan Outstanding + Credit Card Balances/Outstanding
Net Worth = Total Assets - Total Liabilities
Tracks monthly historical snapshots and asset allocation.
"""
from typing import Dict, Any, List
from datetime import date
from database.connection import SessionLocal
from database.models import Account, Investment, Loan
from config.constants import AccountType, LoanStatus

class NetWorthService:
    @staticmethod
    def calculate_current_net_worth() -> Dict[str, Any]:
        return NetWorthService.get_detailed_net_worth()

    @staticmethod
    def get_detailed_net_worth() -> Dict[str, Any]:
        db = SessionLocal()
        try:
            # 1. Liquid Accounts
            accounts = db.query(Account).filter_by(is_active=True).all()
            liquid_accs = [a for a in accounts if a.account_type != AccountType.CREDIT_CARD.value]
            cc_accs = [a for a in accounts if a.account_type == AccountType.CREDIT_CARD.value]

            liquid_assets_paise = sum(a.current_balance_paise for a in liquid_accs)
            cc_liabilities_paise = sum(abs(a.current_balance_paise) for a in cc_accs if a.current_balance_paise < 0)

            # 2. Investments (Mutual Funds, Stocks, Gold, PPF, Real Estate)
            investments = db.query(Investment).all()
            investments_assets_paise = sum(i.current_value_paise for i in investments)

            # 3. Loans Outstanding Principal
            loans = db.query(Loan).filter_by(status=LoanStatus.ACTIVE.value).all()
            loans_liabilities_paise = sum(l.outstanding_principal_paise for l in loans)

            total_assets_paise = liquid_assets_paise + investments_assets_paise
            total_liabilities_paise = loans_liabilities_paise + cc_liabilities_paise
            net_worth_paise = total_assets_paise - total_liabilities_paise

            debt_to_asset_ratio = (total_liabilities_paise / total_assets_paise * 100) if total_assets_paise > 0 else 0

            # Itemized Assets
            asset_items = []
            for a in liquid_accs:
                share = (a.current_balance_paise / total_assets_paise * 100) if total_assets_paise > 0 else 0
                asset_items.append({
                    "id": a.id,
                    "name": a.name,
                    "category": a.account_type,
                    "institution": a.institution_name or "Bank",
                    "value_paise": a.current_balance_paise,
                    "share_pct": round(share, 1),
                    "is_liquid": True
                })
            for inv in investments:
                share = (inv.current_value_paise / total_assets_paise * 100) if total_assets_paise > 0 else 0
                asset_items.append({
                    "id": f"inv_{inv.id}",
                    "name": inv.investment_name,
                    "category": inv.investment_type,
                    "institution": inv.institution or "Portfolio",
                    "value_paise": inv.current_value_paise,
                    "share_pct": round(share, 1),
                    "is_liquid": False
                })

            # Itemized Liabilities
            liability_items = []
            for ln in loans:
                share = (ln.outstanding_principal_paise / total_liabilities_paise * 100) if total_liabilities_paise > 0 else 0
                liability_items.append({
                    "id": f"loan_{ln.id}",
                    "name": ln.loan_name,
                    "category": "Loan",
                    "institution": ln.lender,
                    "value_paise": ln.outstanding_principal_paise,
                    "share_pct": round(share, 1),
                    "rate": ln.interest_rate_percent,
                    "emi_paise": ln.emi_amount_paise
                })
            for cc in cc_accs:
                if cc.current_balance_paise < 0:
                    bal = abs(cc.current_balance_paise)
                    share = (bal / total_liabilities_paise * 100) if total_liabilities_paise > 0 else 0
                    liability_items.append({
                        "id": f"cc_{cc.id}",
                        "name": cc.name,
                        "category": "Credit Card",
                        "institution": cc.institution_name or "Card Issuer",
                        "value_paise": bal,
                        "share_pct": round(share, 1),
                        "rate": 0,
                        "emi_paise": 0
                    })

            # Asset Allocation Categories
            asset_allocation = []
            if total_assets_paise > 0:
                if liquid_assets_paise > 0:
                    asset_allocation.append({
                        "name": "Liquid Accounts & Cash",
                        "amount_paise": liquid_assets_paise,
                        "color": "#38bdf8",
                        "percentage": round(liquid_assets_paise / total_assets_paise * 100, 1)
                    })
                if investments_assets_paise > 0:
                    asset_allocation.append({
                        "name": "Investments & Equities",
                        "amount_paise": investments_assets_paise,
                        "color": "#10b981",
                        "percentage": round(investments_assets_paise / total_assets_paise * 100, 1)
                    })
            else:
                asset_allocation.append({
                    "name": "No Assets Registered",
                    "amount_paise": 0,
                    "color": "#64748b",
                    "percentage": 100
                })

            # Liability Allocation
            liability_allocation = []
            if total_liabilities_paise > 0:
                if loans_liabilities_paise > 0:
                    liability_allocation.append({
                        "name": "Active Term Loans",
                        "amount_paise": loans_liabilities_paise,
                        "color": "#ef4444",
                        "percentage": round(loans_liabilities_paise / total_liabilities_paise * 100, 1)
                    })
                if cc_liabilities_paise > 0:
                    liability_allocation.append({
                        "name": "Credit Card Outstanding",
                        "amount_paise": cc_liabilities_paise,
                        "color": "#f97316",
                        "percentage": round(cc_liabilities_paise / total_liabilities_paise * 100, 1)
                    })
            else:
                liability_allocation.append({
                    "name": "Zero Debt Obligations",
                    "amount_paise": 0,
                    "color": "#10b981",
                    "percentage": 100
                })

            # 6-Month Trajectory
            from analytics.expense_analysis import AnalyticsService
            cash_trend = AnalyticsService.get_cash_flow_trend(months=6)

            points = []
            running_nw = net_worth_paise
            running_assets = total_assets_paise
            running_liab = total_liabilities_paise

            for item in reversed(cash_trend):
                points.append({
                    "month_short": item.get("month_short", "")[:3],
                    "month_label": item.get("month", ""),
                    "net_worth_paise": max(0, running_nw),
                    "assets_paise": max(0, running_assets),
                    "liabilities_paise": max(0, running_liab),
                })
                savings = item.get("savings_paise", 0)
                running_nw -= savings
                running_assets -= savings

            trend_history = list(reversed(points))

            # Solvency Score (0-100)
            if debt_to_asset_ratio == 0:
                solvency_score = 100
                solvency_tier = "Prime Solvency"
                solvency_desc = "Zero debt load. Outstanding financial resilience."
            elif debt_to_asset_ratio < 20:
                solvency_score = 92
                solvency_tier = "Strong Solvency"
                solvency_desc = "Low leverage. Excellent debt coverage."
            elif debt_to_asset_ratio < 45:
                solvency_score = 78
                solvency_tier = "Moderate Solvency"
                solvency_desc = "Manageable debt burden with adequate liquid buffer."
            else:
                solvency_score = 55
                solvency_tier = "High Leverage"
                solvency_desc = "High liability load. Prioritize debt reduction."

            # Runway estimation
            total_spent = sum(c.get("expense_paise", 0) for c in cash_trend)
            avg_monthly_burn = (total_spent // len(cash_trend)) if cash_trend else 0
            if avg_monthly_burn > 0:
                runway_months = round(liquid_assets_paise / avg_monthly_burn, 1)
            else:
                runway_months = 36.0

            return {
                "total_assets_paise": total_assets_paise,
                "total_liabilities_paise": total_liabilities_paise,
                "net_worth_paise": net_worth_paise,
                "debt_to_asset_ratio_pct": round(debt_to_asset_ratio, 1),
                "liquid_assets_paise": liquid_assets_paise,
                "investments_assets_paise": investments_assets_paise,
                "loans_liabilities_paise": loans_liabilities_paise,
                "credit_card_liabilities_paise": cc_liabilities_paise,
                "solvency_score": solvency_score,
                "solvency_tier": solvency_tier,
                "solvency_desc": solvency_desc,
                "runway_months": runway_months,
                "asset_items": asset_items,
                "liability_items": liability_items,
                "asset_allocation": asset_allocation,
                "liability_allocation": liability_allocation,
                "trend_history": trend_history
            }
        finally:
            db.close()
