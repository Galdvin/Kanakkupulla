"""
Report Generation & Export Service:
- Excel (.xlsx) export using Pandas / OpenPyXL
- CSV export
- PDF Financial Summary export using ReportLab
"""
from typing import List, Optional
from datetime import date
from pathlib import Path
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from database.connection import SessionLocal
from database.models import Transaction
from config.constants import TransactionType
from core.financial_utils import format_inr, format_date

class ReportingService:
    @staticmethod
    def export_transactions_to_excel(output_path: Path, start_date: Optional[date] = None, end_date: Optional[date] = None) -> bool:
        db = SessionLocal()
        try:
            q = db.query(Transaction).filter_by(is_deleted=False)
            if start_date:
                q = q.filter(Transaction.transaction_date >= start_date)
            if end_date:
                q = q.filter(Transaction.transaction_date <= end_date)
            txns = q.order_by(Transaction.transaction_date.desc()).all()

            data = []
            for t in txns:
                data.append({
                    "Transaction ID": t.id,
                    "Date": format_date(t.transaction_date),
                    "Type": t.transaction_type,
                    "Kind": t.expense_kind,
                    "Title": t.title,
                    "Category": t.category.name if t.category else "Uncategorized",
                    "Subcategory": t.subcategory.name if t.subcategory else "-",
                    "Amount (₹)": t.amount_paise / 100.0,
                    "Paid By": t.paid_by.full_name if t.paid_by else "-",
                    "Expense For": t.expense_for.full_name if t.expense_for else "-",
                    "Account": t.account.name if t.account else "-",
                    "Payment Method": t.payment_method,
                    "Merchant": t.merchant or "-",
                    "Reference": t.reference_no or "-"
                })

            df = pd.DataFrame(data)
            df.to_excel(output_path, index=False, engine="openpyxl")
            return True
        finally:
            db.close()

    @staticmethod
    def export_transactions_to_csv(output_path: Path, start_date: Optional[date] = None, end_date: Optional[date] = None) -> bool:
        db = SessionLocal()
        try:
            q = db.query(Transaction).filter_by(is_deleted=False)
            if start_date:
                q = q.filter(Transaction.transaction_date >= start_date)
            if end_date:
                q = q.filter(Transaction.transaction_date <= end_date)
            txns = q.order_by(Transaction.transaction_date.desc()).all()

            data = []
            for t in txns:
                data.append({
                    "Transaction ID": t.id,
                    "Date": format_date(t.transaction_date),
                    "Type": t.transaction_type,
                    "Title": t.title,
                    "Category": t.category.name if t.category else "Uncategorized",
                    "Amount (INR)": t.amount_paise / 100.0,
                    "Paid By": t.paid_by.full_name if t.paid_by else "-",
                    "Expense For": t.expense_for.full_name if t.expense_for else "-",
                    "Payment Method": t.payment_method
                })

            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False)
            return True
        finally:
            db.close()

    @staticmethod
    def export_summary_to_pdf(output_path: Path, start_date: Optional[date] = None, end_date: Optional[date] = None) -> bool:
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor("#0284c7"),
            spaceAfter=14
        )
        elements.append(Paragraph("Kanakkupulla - Financial Statement Report", title_style))
        elements.append(Paragraph(f"Period: {format_date(start_date or date(2000, 1, 1))} to {format_date(end_date or date.today())}", styles["Normal"]))
        elements.append(Spacer(1, 15))

        # Recent Transactions Table
        db = SessionLocal()
        try:
            q = db.query(Transaction).filter_by(is_deleted=False)
            if start_date:
                q = q.filter(Transaction.transaction_date >= start_date)
            if end_date:
                q = q.filter(Transaction.transaction_date <= end_date)
            txns = q.order_by(Transaction.transaction_date.desc()).limit(30).all()

            table_data = [["Date", "Type", "Title", "Category", "Paid By", "Amount (₹)"]]
            for t in txns:
                table_data.append([
                    format_date(t.transaction_date),
                    t.transaction_type,
                    t.title[:20],
                    (t.category.name if t.category else "-")[:15],
                    (t.paid_by.full_name if t.paid_by else "-")[:12],
                    f"{t.amount_paise/100:.2f}"
                ])

            t = Table(table_data, colWidths=[70, 60, 120, 100, 80, 80])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]))
            elements.append(t)
            doc.build(elements)
            return True
        finally:
            db.close()
