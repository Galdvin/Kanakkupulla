"""
Loan & EMI Management Service:
Handles accurate EMI calculation using standard financial amortization formulas,
loan tracking, EMI payments, principal/interest breakdown, and liability reduction.
"""
from typing import List, Optional, Tuple, Dict
from datetime import date
import math
from database.connection import SessionLocal
from database.models import Loan, LoanPayment, Account, FamilyMember, AuditLog
from config.constants import LoanStatus
from core.authentication import AuthService

class LoanService:
    @staticmethod
    def calculate_emi_paise(principal_paise: int, annual_rate_pct: float, tenure_months: int) -> int:
        """
        Calculates monthly EMI using standard amortization formula:
        EMI = [P x R x (1+R)^N]/[(1+R)^N-1]
        """
        if annual_rate_pct <= 0 or tenure_months <= 0:
            return int(round(principal_paise / max(1, tenure_months)))

        monthly_rate = (annual_rate_pct / 100.0) / 12.0
        p = float(principal_paise)
        r = monthly_rate
        n = tenure_months

        try:
            factor = math.pow(1 + r, n)
            emi = (p * r * factor) / (factor - 1)
            return int(round(emi))
        except (OverflowError, ZeroDivisionError):
            return int(round(principal_paise / max(1, tenure_months)))

    @staticmethod
    def create_loan(
        loan_name: str,
        lender: str,
        principal_amount_paise: int,
        interest_rate_percent: float,
        loan_start_date: date,
        tenure_months: int,
        family_member_id: Optional[int] = None,
        emi_due_day: int = 5,
        notes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Loan]]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized", None

        loan_name = loan_name.strip()
        if not loan_name:
            return False, "Loan name is required", None

        if principal_amount_paise <= 0:
            return False, "Principal amount must be positive", None

        if tenure_months <= 0:
            return False, "Tenure must be at least 1 month", None

        emi_paise = LoanService.calculate_emi_paise(principal_amount_paise, interest_rate_percent, tenure_months)

        db = SessionLocal()
        try:
            if family_member_id is not None:
                member = db.query(FamilyMember).filter_by(id=family_member_id).first()
                if not member:
                    return False, "Selected family member not found", None

            loan = Loan(
                loan_name=loan_name,
                lender=lender.strip(),
                principal_amount_paise=principal_amount_paise,
                interest_rate_percent=interest_rate_percent,
                loan_start_date=loan_start_date,
                tenure_months=tenure_months,
                family_member_id=family_member_id,
                emi_amount_paise=emi_paise,
                emi_due_day=emi_due_day,
                outstanding_principal_paise=principal_amount_paise,
                status=LoanStatus.ACTIVE.value,
                notes=notes
            )
            db.add(loan)
            db.commit()
            db.refresh(loan)
            db.expunge(loan)
            return True, "Loan created successfully", loan
        except Exception as e:
            db.rollback()
            return False, str(e), None
        finally:
            db.close()

    @staticmethod
    def record_emi_payment(
        loan_id: int,
        amount_paise: int,
        payment_date: date,
        account_id: int,
        payment_method: str = "Bank Transfer",
        reference: Optional[str] = None
    ) -> Tuple[bool, str]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized"

        if amount_paise <= 0:
            return False, "Payment amount must be positive"

        db = SessionLocal()
        try:
            loan = db.query(Loan).filter_by(id=loan_id).first()
            acc = db.query(Account).filter_by(id=account_id).first()

            if not loan or not acc:
                return False, "Invalid loan or payment account"

            # 1. Deduct from paying account
            acc.current_balance_paise -= amount_paise

            # 2. Amortization interest vs principal breakdown
            monthly_rate = (loan.interest_rate_percent / 100.0) / 12.0
            interest_component = int(round(loan.outstanding_principal_paise * monthly_rate))
            # Interest cannot exceed total payment
            interest_component = min(interest_component, amount_paise)
            principal_component = max(0, amount_paise - interest_component)

            # 3. Reduce outstanding principal
            loan.outstanding_principal_paise = max(0, loan.outstanding_principal_paise - principal_component)
            if loan.outstanding_principal_paise == 0:
                loan.status = LoanStatus.CLOSED.value

            # 4. Record loan payment history
            payment = LoanPayment(
                loan_id=loan_id,
                payment_date=payment_date,
                amount_paise=amount_paise,
                principal_component_paise=principal_component,
                interest_component_paise=interest_component,
                payment_method=payment_method,
                reference=reference
            )
            db.add(payment)

            db.commit()
            return True, "EMI payment recorded successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    @staticmethod
    def delete_loan(loan_id: int) -> Tuple[bool, str]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized"

        db = SessionLocal()
        try:
            loan = db.query(Loan).filter_by(id=loan_id).first()
            if not loan:
                return False, "Loan not found"
            db.delete(loan)
            db.commit()
            return True, "Loan deleted successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    @staticmethod
    def get_all_loans(family_member_id: Optional[int] = None) -> List[Loan]:
        db = SessionLocal()
        try:
            query = db.query(Loan)
            if family_member_id is not None:
                query = query.filter((Loan.family_member_id == family_member_id) | (Loan.family_member_id == None))
            results = query.order_by(Loan.status, Loan.loan_name).all()
            for l in results:
                if l.family_member:
                    _ = l.family_member.name
                _ = l.payments
                db.expunge(l)
            return results
        finally:
            db.close()

    @staticmethod
    def get_loan_summary(family_member_id: Optional[int] = None) -> Dict:
        loans = LoanService.get_all_loans(family_member_id)
        active_loans = [l for l in loans if l.status == LoanStatus.ACTIVE.value]
        total_principal = sum(l.principal_amount_paise for l in loans)
        total_outstanding = sum(l.outstanding_principal_paise for l in active_loans)
        monthly_emi = sum(l.emi_amount_paise for l in active_loans)

        return {
            "total_principal_paise": total_principal,
            "total_outstanding_paise": total_outstanding,
            "monthly_emi_paise": monthly_emi,
            "total_loans_count": len(loans),
            "active_loans_count": len(active_loans),
            "closed_loans_count": len(loans) - len(active_loans)
        }
