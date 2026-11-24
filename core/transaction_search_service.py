"""
Phase 2 Comprehensive Transaction Search & Multi-Criteria Filtering Engine:
Filters by:
- Family member (payer or beneficiary)
- Category & Subcategory
- Account & Payment mode
- Transaction type (Daily expense, Occasional expense, Income)
- Search text (Title, description, merchant, reference no)
- Date range (from - to)
- Min and Max amounts
"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import date
from database.connection import SessionLocal
from database.models import FinancialTransaction
from config.constants import TransactionType

class TransactionSearchService:
    @staticmethod
    def search_transactions(
        keyword: Optional[str] = None,
        transaction_type: Optional[str] = None,
        expense_kind: Optional[str] = None,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        account_id: Optional[int] = None,
        paid_by_member_id: Optional[int] = None,
        expense_for_member_id: Optional[int] = None,
        payment_method: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_amount_paise: Optional[int] = None,
        max_amount_paise: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[FinancialTransaction], int, int]:
        """
        Returns:
        (transactions, total_count, total_sum_paise)
        """
        db = SessionLocal()
        try:
            q = db.query(FinancialTransaction).filter(FinancialTransaction.is_deleted == False)

            if keyword and keyword.strip():
                kw = f"%{keyword.strip()}%"
                q = q.filter(
                    (FinancialTransaction.title.ilike(kw)) |
                    (FinancialTransaction.description.ilike(kw)) |
                    (FinancialTransaction.merchant.ilike(kw)) |
                    (FinancialTransaction.reference_no.ilike(kw)) |
                    (FinancialTransaction.event_name.ilike(kw))
                )

            if transaction_type:
                q = q.filter(FinancialTransaction.transaction_type == transaction_type)
            if expense_kind:
                q = q.filter(FinancialTransaction.expense_kind == expense_kind)
            if category_id:
                q = q.filter(FinancialTransaction.category_id == category_id)
            if subcategory_id:
                q = q.filter(FinancialTransaction.subcategory_id == subcategory_id)
            if account_id:
                q = q.filter(FinancialTransaction.account_id == account_id)
            if paid_by_member_id:
                q = q.filter(FinancialTransaction.paid_by_member_id == paid_by_member_id)
            if expense_for_member_id:
                q = q.filter(FinancialTransaction.expense_for_member_id == expense_for_member_id)
            if payment_method:
                q = q.filter(FinancialTransaction.payment_method == payment_method)
            if start_date:
                q = q.filter(FinancialTransaction.transaction_date >= start_date)
            if end_date:
                q = q.filter(FinancialTransaction.transaction_date <= end_date)
            if min_amount_paise is not None:
                q = q.filter(FinancialTransaction.amount_paise >= min_amount_paise)
            if max_amount_paise is not None:
                q = q.filter(FinancialTransaction.amount_paise <= max_amount_paise)

            total_count = q.count()
            all_matching = q.all()
            total_sum_paise = sum(t.amount_paise for t in all_matching)

            paginated = q.order_by(
                FinancialTransaction.transaction_date.desc(), 
                FinancialTransaction.id.desc()
            ).offset(offset).limit(limit).all()

            for t in paginated:
                _ = t.category.name if t.category else None
                _ = t.subcategory.name if t.subcategory else None
                _ = t.account.name if t.account else None
                _ = t.paid_by_member.name if t.paid_by_member else None
                _ = t.expense_for_member.name if t.expense_for_member else None
                _ = len(t.attachments)
                db.expunge(t)

            return paginated, total_count, total_sum_paise
        finally:
            db.close()
