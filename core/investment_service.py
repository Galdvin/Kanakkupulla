"""
Investment Management Service:
Tracks Mutual Funds, Stocks, SIPs, Gold, EPF/PPF, FDs, and portfolio returns
for individual family members and family aggregate holdings.
"""
from typing import List, Optional, Tuple, Dict
from datetime import date
from database.connection import SessionLocal
from database.models import Investment, FamilyMember, AuditLog
from core.authentication import AuthService

class InvestmentService:
    @staticmethod
    def add_investment(
        family_member_id: int,
        investment_name: str,
        investment_type: str,
        invested_amount_paise: int,
        current_value_paise: int,
        investment_date: date,
        maturity_date: Optional[date] = None,
        institution: Optional[str] = None,
        folio_or_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Investment]]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized", None

        investment_name = investment_name.strip()
        if not investment_name:
            return False, "Investment name is required", None

        if invested_amount_paise <= 0:
            return False, "Invested amount must be positive", None

        if current_value_paise < 0:
            return False, "Current value cannot be negative", None

        db = SessionLocal()
        try:
            member = db.query(FamilyMember).filter_by(id=family_member_id).first()
            if not member:
                return False, "Invalid family member selected", None

            inv = Investment(
                family_member_id=family_member_id,
                investment_name=investment_name,
                investment_type=investment_type,
                invested_amount_paise=invested_amount_paise,
                current_value_paise=current_value_paise,
                investment_date=investment_date,
                maturity_date=maturity_date,
                institution=institution,
                folio_or_id=folio_or_id,
                notes=notes,
                last_valuation_date=date.today()
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

        if new_value_paise < 0:
            return False, "Current value cannot be negative"

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
    def delete_investment(investment_id: int) -> Tuple[bool, str]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized"

        db = SessionLocal()
        try:
            inv = db.query(Investment).filter_by(id=investment_id).first()
            if not inv:
                return False, "Investment not found"
            db.delete(inv)
            db.commit()
            return True, "Investment deleted successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    @staticmethod
    def get_portfolio_summary(family_member_id: Optional[int] = None) -> Dict:
        investments = InvestmentService.get_all_investments(family_member_id)
        total_invested = sum(i.invested_amount_paise for i in investments)
        total_current = sum(i.current_value_paise for i in investments)
        unrealized_gain = total_current - total_invested
        returns_pct = (unrealized_gain / total_invested * 100) if total_invested > 0 else 0

        # Breakdown by asset type
        allocation: Dict[str, int] = {}
        for inv in investments:
            allocation[inv.investment_type] = allocation.get(inv.investment_type, 0) + inv.current_value_paise

        return {
            "total_invested_paise": total_invested,
            "total_current_paise": total_current,
            "unrealized_gain_paise": unrealized_gain,
            "returns_pct": round(returns_pct, 2),
            "count": len(investments),
            "asset_allocation": allocation
        }

    @staticmethod
    def get_all_investments(family_member_id: Optional[int] = None) -> List[Investment]:
        db = SessionLocal()
        try:
            query = db.query(Investment)
            if family_member_id is not None:
                query = query.filter_by(family_member_id=family_member_id)
            results = query.order_by(Investment.investment_date.desc()).all()
            for r in results:
                if r.family_member:
                    _ = r.family_member.name
                db.expunge(r)
            return results
        finally:
            db.close()
