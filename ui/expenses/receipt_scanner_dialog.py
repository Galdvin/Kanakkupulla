"""
Smart Receipt Scanner Dialog:
Upload an image of a bill/receipt, automatically extract merchant, date, amount, category,
and allow user review before one-click entry into Daily Expenses.
"""
from ui.expenses.ocr_receipt_dialog import SmartReceiptReviewDialog

# Backward-compatibility alias
SmartReceiptDialog = SmartReceiptReviewDialog

__all__ = ["SmartReceiptDialog", "SmartReceiptReviewDialog"]
