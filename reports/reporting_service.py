"""
Comprehensive Financial Reporting & Export Engine:
- Multi-tab Excel (.xlsx) export with summary KPIs, full transactions, and category breakdowns.
- Professional PDF Financial Summary export using ReportLab with executive KPIs, category distribution, and member attribution.
- CSV export.
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime
from pathlib import Path
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from database.connection import SessionLocal
from database.models import (
    FinancialTransaction, Category, FamilyMember, Account, FamilyProfile
)
from config.constants import TransactionType
from core.financial_utils import format_inr, format_date

class ReportingService:
    @staticmethod
    def get_financial_report(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        member_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculates aggregate reporting metrics, category distribution,
        and family member attribution for the given date range and scope.
        """
        db = SessionLocal()
        try:
            fam = db.query(FamilyProfile).first()
            family_name = fam.family_name if fam else "My Household"

            q = db.query(FinancialTransaction).filter(
                FinancialTransaction.is_deleted == False
            )
            if start_date:
                q = q.filter(FinancialTransaction.transaction_date >= start_date)
            if end_date:
                q = q.filter(FinancialTransaction.transaction_date <= end_date)
            if member_id is not None:
                q = q.filter(
                    (FinancialTransaction.paid_by_member_id == member_id) |
                    (FinancialTransaction.expense_for_member_id == member_id)
                )

            txns = q.order_by(FinancialTransaction.transaction_date.desc()).all()

            total_income_paise = sum(t.amount_paise for t in txns if t.transaction_type == TransactionType.INCOME.value)
            total_expense_paise = sum(t.amount_paise for t in txns if t.transaction_type == TransactionType.EXPENSE.value)
            net_savings_paise = total_income_paise - total_expense_paise
            savings_rate_pct = round((net_savings_paise / total_income_paise * 100), 1) if total_income_paise > 0 else 0

            # Category Breakdown
            cat_map: Dict[str, Dict[str, Any]] = {}
            for t in txns:
                if t.transaction_type == TransactionType.EXPENSE.value:
                    cat_name = t.category.name if t.category else "Uncategorized"
                    if cat_name not in cat_map:
                        cat_map[cat_name] = {"name": cat_name, "total_paise": 0, "count": 0}
                    cat_map[cat_name]["total_paise"] += t.amount_paise
                    cat_map[cat_name]["count"] += 1

            category_breakdown = list(cat_map.values())
            category_breakdown.sort(key=lambda x: x["total_paise"], reverse=True)
            for c in category_breakdown:
                c["percentage"] = round((c["total_paise"] / total_expense_paise * 100), 1) if total_expense_paise > 0 else 0

            # Member Attribution (Payer vs Beneficiary)
            members = db.query(FamilyMember).all()
            member_attribution = []
            for m in members:
                paid_paise = sum(t.amount_paise for t in txns if t.paid_by_member_id == m.id and t.transaction_type == TransactionType.EXPENSE.value)
                benefited_paise = sum(t.amount_paise for t in txns if t.expense_for_member_id == m.id and t.transaction_type == TransactionType.EXPENSE.value)
                if paid_paise > 0 or benefited_paise > 0:
                    member_attribution.append({
                        "member_id": m.id,
                        "name": m.name,
                        "relation": m.relation_type,
                        "paid_paise": paid_paise,
                        "benefited_paise": benefited_paise,
                        "net_contribution_paise": paid_paise - benefited_paise
                    })

            # Extract detached transaction data dicts
            txn_records = []
            for t in txns:
                txn_records.append({
                    "id": t.id,
                    "transaction_date": t.transaction_date,
                    "transaction_type": t.transaction_type,
                    "expense_kind": t.expense_kind,
                    "title": t.title,
                    "category_name": t.category.name if t.category else "Uncategorized",
                    "subcategory_name": t.subcategory.name if t.subcategory else "-",
                    "amount_paise": t.amount_paise,
                    "paid_by_name": t.paid_by_member.name if t.paid_by_member else "-",
                    "expense_for_name": t.expense_for_member.name if t.expense_for_member else "-",
                    "account_name": t.account.name if t.account else "-",
                    "payment_method": t.payment_method,
                    "merchant": t.merchant or "-",
                    "reference_no": t.reference_no or "-"
                })

            return {
                "family_name": family_name,
                "start_date": start_date,
                "end_date": end_date,
                "total_income_paise": total_income_paise,
                "total_expense_paise": total_expense_paise,
                "net_savings_paise": net_savings_paise,
                "savings_rate_pct": savings_rate_pct,
                "transaction_count": len(txns),
                "category_breakdown": category_breakdown,
                "member_attribution": member_attribution,
                "transactions": txn_records
            }
        finally:
            db.close()

    @staticmethod
    def export_transactions_to_excel(
        output_path: Path,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        member_id: Optional[int] = None
    ) -> bool:
        """
        Creates a multi-tab Excel workbook containing:
        1. Executive Summary & KPIs
        2. Transactions Ledger
        3. Category Breakdown
        4. Family Attribution
        """
        report = ReportingService.get_financial_report(start_date, end_date, member_id)
        txns = report["transactions"]

        # Tab 1: Executive Summary
        summary_rows = [
            {"Metric": "Family Name", "Value": report["family_name"]},
            {"Metric": "Report Period", "Value": f"{format_date(start_date) if start_date else 'Beginning'} to {format_date(end_date) if end_date else 'Present'}"},
            {"Metric": "Total Income (₹)", "Value": report["total_income_paise"] / 100.0},
            {"Metric": "Total Expenditure (₹)", "Value": report["total_expense_paise"] / 100.0},
            {"Metric": "Net Savings Surplus (₹)", "Value": report["net_savings_paise"] / 100.0},
            {"Metric": "Savings Rate (%)", "Value": f"{report['savings_rate_pct']}%"},
            {"Metric": "Total Recorded Transactions", "Value": report["transaction_count"]},
            {"Metric": "Generated On", "Value": datetime.now().strftime("%d-%m-%Y %H:%M:%S")}
        ]
        df_summary = pd.DataFrame(summary_rows)

        # Tab 2: All Transactions
        txn_data = []
        for t in txns:
            txn_data.append({
                "Txn ID": t["id"],
                "Date": format_date(t["transaction_date"]),
                "Type": t["transaction_type"],
                "Kind": t["expense_kind"],
                "Title": t["title"],
                "Category": t["category_name"],
                "Subcategory": t["subcategory_name"],
                "Amount (₹)": t["amount_paise"] / 100.0,
                "Paid By": t["paid_by_name"],
                "Expense For": t["expense_for_name"],
                "Account": t["account_name"],
                "Payment Method": t["payment_method"],
                "Merchant": t["merchant"],
                "Reference": t["reference_no"]
            })
        df_txns = pd.DataFrame(txn_data) if txn_data else pd.DataFrame(columns=["No Transactions Found"])

        # Tab 3: Category Breakdown
        cat_rows = []
        for c in report["category_breakdown"]:
            cat_rows.append({
                "Category": c["name"],
                "Total Spent (₹)": c["total_paise"] / 100.0,
                "Transaction Count": c["count"],
                "Share of Expenses (%)": c["percentage"]
            })
        df_cats = pd.DataFrame(cat_rows) if cat_rows else pd.DataFrame(columns=["Category", "Total Spent (₹)", "Transaction Count", "Share (%)"])

        # Tab 4: Member Attribution
        member_rows = []
        for m in report["member_attribution"]:
            member_rows.append({
                "Family Member": m["name"],
                "Relationship": m["relation"],
                "Total Paid (₹)": m["paid_paise"] / 100.0,
                "Total Benefited (₹)": m["benefited_paise"] / 100.0,
                "Net Contribution (₹)": m["net_contribution_paise"] / 100.0
            })
        df_members = pd.DataFrame(member_rows) if member_rows else pd.DataFrame(columns=["Member", "Paid (₹)", "Benefited (₹)", "Net (₹)"])

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df_summary.to_excel(writer, sheet_name="Executive Summary", index=False)
            df_txns.to_excel(writer, sheet_name="Transactions Ledger", index=False)
            df_cats.to_excel(writer, sheet_name="Category Breakdown", index=False)
            df_members.to_excel(writer, sheet_name="Family Attribution", index=False)

        return True

    @staticmethod
    def export_summary_to_pdf(
        output_path: Path,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        member_id: Optional[int] = None
    ) -> bool:
        """
        Generates a publication-grade PDF report using ReportLab.
        Contains branded headers, executive KPI summary table,
        category distribution table, and recent transaction log.
        """
        report = ReportingService.get_financial_report(start_date, end_date, member_id)
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        styles = getSampleStyleSheet()
        elements = []

        # Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0284c7"),
            fontName="Helvetica-Bold"
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#64748b")
        )
        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
            spaceBefore=14,
            spaceAfter=6
        )
        cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#334155")
        )
        cell_bold = ParagraphStyle(
            'TableCellBold',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold"
        )

        # Header Block
        elements.append(Paragraph("Kanakkupulla (கணக்குப்புள்ள)", title_style))
        period_str = f"{format_date(start_date) if start_date else 'Beginning'} to {format_date(end_date) if end_date else 'Present'}"
        elements.append(Paragraph(f"Family Financial Statement  |  {report['family_name']}  |  Period: {period_str}", subtitle_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=14))

        # 1. Executive Summary Table
        elements.append(Paragraph("1. Executive Financial Summary", h2_style))
        inc_str = f"INR {report['total_income_paise'] / 100:,.2f}"
        exp_str = f"INR {report['total_expense_paise'] / 100:,.2f}"
        sav_str = f"INR {report['net_savings_paise'] / 100:,.2f}"
        rate_str = f"{report['savings_rate_pct']}%"

        kpi_data = [
            [
                Paragraph("<b>Total Income</b>", cell_style),
                Paragraph("<b>Total Expenditure</b>", cell_style),
                Paragraph("<b>Net Savings Surplus</b>", cell_style),
                Paragraph("<b>Savings Rate</b>", cell_style)
            ],
            [
                Paragraph(f"<font color='#059669' size='12'><b>{inc_str}</b></font>", cell_style),
                Paragraph(f"<font color='#e11d48' size='12'><b>{exp_str}</b></font>", cell_style),
                Paragraph(f"<font color='#0284c7' size='12'><b>{sav_str}</b></font>", cell_style),
                Paragraph(f"<font color='#0891b2' size='12'><b>{rate_str}</b></font>", cell_style)
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[130, 130, 140, 120])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 14))

        # 2. Category Breakdown Table
        elements.append(Paragraph("2. Expense Distribution by Category", h2_style))
        cat_data = [[
            Paragraph("Category", cell_bold),
            Paragraph("Transaction Count", cell_bold),
            Paragraph("Total Amount (INR)", cell_bold),
            Paragraph("Share of Budget", cell_bold)
        ]]
        for c in report["category_breakdown"][:8]: # Top 8 categories
            cat_data.append([
                Paragraph(c["name"], cell_style),
                Paragraph(str(c["count"]), cell_style),
                Paragraph(f"INR {c['total_paise'] / 100:,.2f}", cell_style),
                Paragraph(f"{c['percentage']}%", cell_style)
            ])
        if not report["category_breakdown"]:
            cat_data.append([Paragraph("No expenses recorded in this period", cell_style), Paragraph("-", cell_style), Paragraph("-", cell_style), Paragraph("-", cell_style)])

        cat_table = Table(cat_data, colWidths=[180, 110, 130, 100])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(cat_table)
        elements.append(Spacer(1, 14))

        # 3. Family Attribution Table
        elements.append(Paragraph("3. Family Member Contribution & Beneficiary Attribution", h2_style))
        member_data = [[
            Paragraph("Family Member", cell_bold),
            Paragraph("Role / Relation", cell_bold),
            Paragraph("Total Paid (INR)", cell_bold),
            Paragraph("Benefited (INR)", cell_bold),
            Paragraph("Net Contribution", cell_bold)
        ]]
        for m in report["member_attribution"]:
            net_val = m["net_contribution_paise"]
            net_color = "#059669" if net_val >= 0 else "#e11d48"
            member_data.append([
                Paragraph(m["name"], cell_style),
                Paragraph(m["relation"], cell_style),
                Paragraph(f"INR {m['paid_paise'] / 100:,.2f}", cell_style),
                Paragraph(f"INR {m['benefited_paise'] / 100:,.2f}", cell_style),
                Paragraph(f"<font color='{net_color}'>INR {net_val / 100:,.2f}</font>", cell_style)
            ])
        if not report["member_attribution"]:
            member_data.append([Paragraph("No member attribution data", cell_style), Paragraph("-", cell_style), Paragraph("-", cell_style), Paragraph("-", cell_style), Paragraph("-", cell_style)])

        member_table = Table(member_data, colWidths=[130, 100, 100, 100, 90])
        member_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(member_table)
        elements.append(Spacer(1, 14))

        # 4. Recent Transactions Log
        elements.append(Paragraph("4. Recent Transactions Sample", h2_style))
        txn_data_sample = [[
            Paragraph("Date", cell_bold),
            Paragraph("Title", cell_bold),
            Paragraph("Category", cell_bold),
            Paragraph("Account", cell_bold),
            Paragraph("Amount (INR)", cell_bold)
        ]]
        for t in report["transactions"][:10]: # First 10
            t_col = "#e11d48" if t["transaction_type"] == "Expense" else "#059669"
            txn_data_sample.append([
                Paragraph(format_date(t["transaction_date"]), cell_style),
                Paragraph(t["title"][:24], cell_style),
                Paragraph(t["category_name"], cell_style),
                Paragraph(t["account_name"], cell_style),
                Paragraph(f"<font color='{t_col}'>INR {t['amount_paise'] / 100:,.2f}</font>", cell_style)
            ])
        if not report["transactions"]:
            txn_data_sample.append([Paragraph("No transactions recorded", cell_style), Paragraph("-", cell_style), Paragraph("-", cell_style), Paragraph("-", cell_style), Paragraph("-", cell_style)])

        recent_table = Table(txn_data_sample, colWidths=[80, 140, 110, 100, 90])
        recent_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(recent_table)

        # Footer note
        elements.append(Spacer(1, 16))
        footer_text = f"Report generated on {datetime.now().strftime('%d-%m-%Y at %H:%M:%S')} UTC by Kanakkupulla Desktop App."
        elements.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor("#94a3b8"), alignment=1)))

        doc.build(elements)
        return True

    @staticmethod
    def export_transactions_to_csv(
        output_path: Path,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        member_id: Optional[int] = None
    ) -> bool:
        report = ReportingService.get_financial_report(start_date, end_date, member_id)
        txns = report["transactions"]
        data = []
        for t in txns:
            data.append({
                "Transaction ID": t["id"],
                "Date": format_date(t["transaction_date"]),
                "Type": t["transaction_type"],
                "Title": t["title"],
                "Category": t["category_name"],
                "Amount (INR)": t["amount_paise"] / 100.0,
                "Paid By": t["paid_by_name"],
                "Expense For": t["expense_for_name"],
                "Payment Method": t["payment_method"]
            })
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        return True
