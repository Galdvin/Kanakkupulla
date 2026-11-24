"""
Daily Spending Heatmap Data Engine:
Computes daily expenditure totals for any given year/month and classifies spending intensity
(e.g., Level 0: zero spending, Level 1: <₹1,000, Level 2: ₹1,000-₹3,000, Level 3: ₹3,000-₹8,000, Level 4: >₹8,000).
"""
from typing import Dict, Any, List
from datetime import date, timedelta
from database.connection import SessionLocal
from database.models import Transaction
from config.constants import TransactionType

class HeatmapService:
    @staticmethod
    def get_spending_heatmap(year: int, month: int) -> Dict[str, Any]:
        """
        Returns day-wise spending totals and normalized intensity (0-4)
        """
        db = SessionLocal()
        try:
            first_day = date(year, month, 1)
            # Find last day of month
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)

            expenses = db.query(Transaction).filter(
                Transaction.transaction_type == TransactionType.EXPENSE.value,
                Transaction.is_deleted == False,
                Transaction.transaction_date >= first_day,
                Transaction.transaction_date <= last_day
            ).all()

            daily_map: Dict[int, int] = {d: 0 for d in range(1, last_day.day + 1)}
            for e in expenses:
                d = e.transaction_date.day
                daily_map[d] = daily_map.get(d, 0) + e.amount_paise

            # Classify intensity
            heatmap_days = []
            max_daily_paise = max(daily_map.values()) if daily_map.values() else 0

            for day, total_paise in daily_map.items():
                if total_paise == 0:
                    level = 0
                elif total_paise < 100000: # < ₹1,000
                    level = 1
                elif total_paise < 300000: # ₹1,000 - ₹3,000
                    level = 2
                elif total_paise < 800000: # ₹3,000 - ₹8,000
                    level = 3
                else: # > ₹8,000
                    level = 4

                heatmap_days.append({
                    "day": day,
                    "date": f"{year}-{month:02d}-{day:02d}",
                    "total_paise": total_paise,
                    "intensity_level": level # 0, 1, 2, 3, 4
                })

            return {
                "year": year,
                "month": month,
                "days": heatmap_days,
                "month_total_paise": sum(daily_map.values()),
                "highest_day_paise": max_daily_paise
            }
        finally:
            db.close()
