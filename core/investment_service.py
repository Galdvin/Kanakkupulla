"""
Investment Management Service:
Tracks Mutual Funds, Stocks, SIPs, Gold, EPF/PPF, FDs, and portfolio returns.
"""
from typing import List, Optional, Tuple, Dict
from datetime import date
from database.connection import SessionLocal
from database.models import Investment, AuditLog
from core.authentication import AuthService

class InvestmentService:
    @staticmethod
    def add_investment(
        user_id: int,
        investment_name: str,
        investment_type: str,
        invested_amount_paise: int,
        current_value_paise: int,
        investment_date: date,
        maturity_date: Optional[date] = None,
        institution: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Investment]]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized", None

        if invested_amount_paise <= 0:
            return False, "Invested amount must be positive", None

        db = SessionLocal()
        try:
            inv = Investment(
                user_id=user_id,
                investment_name=investment_name.strip(),
                investment_type=investment_type,
                invested_amount_paise=invested_amount_paise,
                current_value_paise=current_value_paise,
                investment_date=investment_date,
                maturity_date=maturity_date,
                institution=institution,
                notes=notes
            )
            db.add(inv)
            db.commit()
            db.refresh(inv)
            db.expunge(inv)
            return True, "Investment added successfully", inv
        except Exception as e:
            db.rollback()
            return False, str(e), None
        finally:
            db.close()

    @staticmethod
    def update_valuation(investment_id: int, new_value_paise: int) -> Tuple[bool, str]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized"

        db = SessionLocal()
        try:
            inv = db.query(Investment).filter_by(id=investment_id).first()
            if not inv:
                return False, "Investment not found"

            inv.current_value_paise = new_value_paise
            inv.last_valuation_date = date.today()
            db.commit()
            return True, "Valuation updated successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    @staticmethod
    def get_portfolio_summary() -> Dict:
        db = SessionLocal()
        try:
            investments = db.query(Investment).all()
            total_invested = sum(i.invested_amount_paise for i in investments)
            total_current = sum(i.current_value_paise for i in investments)
            unrealized_gain = total_current - total_invested
            returns_pct = (unrealized_gain / total_invested * 100) if total_invested > 0 else 0

            return {
                "total_invested_paise": total_invested,
                "total_current_paise": total_current,
                "unrealized_gain_paise": unrealized_gain,
                "returns_pct": round(returns_pct, 2),
                "count": len(investments)
            }
        finally:
            db.close()

    @staticmethod
    def get_all_investments() -> List[Investment]:
        db = SessionLocal()
        try:
            results = db.query(Investment).order_by(Investment.investment_date.desc()).all()
            for r in results:
                _ = r.user.full_name if r.user else None
                db.expunge(r)
            return results
        finally:
            db.close()
