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
        db = SessionLocal()
        try:
            # 1. Liquid Accounts
            accounts = db.query(Account).filter_by(is_active=True).all()
            liquid_assets_paise = sum(a.current_balance_paise for a in accounts if a.account_type != AccountType.CREDIT_CARD.value)
            
            # Credit card debt (negative balance or spent portion)
            cc_liabilities_paise = sum(abs(a.current_balance_paise) for a in accounts if a.account_type == AccountType.CREDIT_CARD.value and a.current_balance_paise < 0)

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

            return {
                "total_assets_paise": total_assets_paise,
                "total_liabilities_paise": total_liabilities_paise,
                "net_worth_paise": net_worth_paise,
                "liquid_assets_paise": liquid_assets_paise,
                "investments_assets_paise": investments_assets_paise,
                "loans_liabilities_paise": loans_liabilities_paise,
                "credit_card_liabilities_paise": cc_liabilities_paise,
                "debt_to_asset_ratio_pct": round(debt_to_asset_ratio, 1)
            }
        finally:
            db.close()
