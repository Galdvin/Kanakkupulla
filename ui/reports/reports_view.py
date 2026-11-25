"""
Financial Reports & Analytics View:
Displays executive summaries, category-wise breakdowns, and family member attribution.
Exports professional PDF statements and multi-tab Excel workbooks.
"""
from typing import Optional
from pathlib import Path
from datetime import date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QFileDialog, QSplitter
)
from PySide6.QtCore import Qt, QDate
from reports.reporting_service import ReportingService
from core.family_service import FamilyService

class ReportsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(14)

        # Header Bar
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Reports & Financial Analytics")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #f8fafc;")
        sub_lbl = QLabel("Generate day-wise, month-wise, and category reports. Export publication-quality PDF and Excel files.")
        sub_lbl.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Export Buttons
        pdf_btn = QPushButton("📄 Export PDF Statement")
        pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #f43f5e; color: white; font-weight: 600;
                padding: 8px 16px; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #e11d48; }
        """)
        pdf_btn.clicked.connect(self.export_pdf)
        header_layout.addWidget(pdf_btn)

        excel_btn = QPushButton("📊 Export Excel Workbook")
        excel_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f766e; color: white; font-weight: 600;
                padding: 8px 16px; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #0d9488; }
        """)
        excel_btn.clicked.connect(self.export_excel)
        header_layout.addWidget(excel_btn)

        self.layout.addLayout(header_layout)

        # Filter Bar Frame
        filter_frame = QFrame()
        filter_frame.setStyleSheet("background-color: #1e293b; border-radius: 8px; padding: 10px 16px; border: 1px solid #334155;")
        filter_lay = QHBoxLayout(filter_frame)
        filter_lay.setSpacing(14)

        # Period preset selector
        filter_lay.addWidget(QLabel("Period:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["This Month", "Last Month", "This Quarter", "This Year", "All Time", "Custom"])
        self.period_combo.currentIndexChanged.connect(self.on_period_changed)
        self.period_combo.setStyleSheet("background-color: #0f172a; color: #f8fafc; padding: 6px 10px; border-radius: 4px; border: 1px solid #334155;")
        filter_lay.addWidget(self.period_combo)

        # Dates
        filter_lay.addWidget(QLabel("From:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        today = date.today()
        self.start_date_edit.setDate(QDate(today.year, today.month, 1))
        self.start_date_edit.setStyleSheet("background-color: #0f172a; color: #f8fafc; padding: 6px 10px; border-radius: 4px; border: 1px solid #334155;")
        filter_lay.addWidget(self.start_date_edit)

        filter_lay.addWidget(QLabel("To:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate(today.year, today.month, today.day))
        self.end_date_edit.setStyleSheet("background-color: #0f172a; color: #f8fafc; padding: 6px 10px; border-radius: 4px; border: 1px solid #334155;")
        filter_lay.addWidget(self.end_date_edit)

        # Member filter
        filter_lay.addWidget(QLabel("Member:"))
        self.member_combo = QComboBox()
        self.member_combo.addItem("All Family", None)
        members = FamilyService.get_all_members()
        for m in members:
            self.member_combo.addItem(f"👤 {m.name}", m.id)
        self.member_combo.setStyleSheet("background-color: #0f172a; color: #f8fafc; padding: 6px 10px; border-radius: 4px; border: 1px solid #334155;")
        filter_lay.addWidget(self.member_combo)

        apply_btn = QPushButton("Apply Filter")
        apply_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: 600; padding: 6px 14px; border-radius: 4px;")
        apply_btn.clicked.connect(self.load_data)
        filter_lay.addWidget(apply_btn)
        filter_lay.addStretch()

        self.layout.addWidget(filter_frame)

        # KPI Summary Cards Bar
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(16)
        self.layout.addLayout(self.kpi_layout)

        # Splitter: Left Category Breakdown, Right Member Attribution
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #334155; width: 2px; }")

        # Category Table Box
        cat_box = QFrame()
        cat_box.setStyleSheet("background-color: #1e293b; border-radius: 8px; border: 1px solid #334155; padding: 12px;")
        cat_lay = QVBoxLayout(cat_box)
        cat_title = QLabel("Category-Wise Expense Distribution")
        cat_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #38bdf8;")
        cat_lay.addWidget(cat_title)

        self.cat_table = QTableWidget()
        self.cat_table.setColumnCount(4)
        self.cat_table.setHorizontalHeaderLabels(["Category", "Count", "Total (₹)", "Share"])
        self.cat_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 4):
            self.cat_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.cat_table.setStyleSheet("background-color: #0f172a; border: 1px solid #334155; gridline-color: #334155; color: #f8fafc;")
        cat_lay.addWidget(self.cat_table)
        splitter.addWidget(cat_box)

        # Member Table Box
        member_box = QFrame()
        member_box.setStyleSheet("background-color: #1e293b; border-radius: 8px; border: 1px solid #334155; padding: 12px;")
        mem_lay = QVBoxLayout(member_box)
        mem_title = QLabel("Family Member Attribution (Payer vs Beneficiary)")
        mem_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #10b981;")
        mem_lay.addWidget(mem_title)

        self.member_table = QTableWidget()
        self.member_table.setColumnCount(5)
        self.member_table.setHorizontalHeaderLabels(["Member", "Role", "Paid (₹)", "Benefited (₹)", "Net (₹)"])
        self.member_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 5):
            self.member_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.member_table.setStyleSheet("background-color: #0f172a; border: 1px solid #334155; gridline-color: #334155; color: #f8fafc;")
        mem_lay.addWidget(self.member_table)
        splitter.addWidget(member_box)

        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 5)
        self.layout.addWidget(splitter)

        self.load_data()

    def on_period_changed(self):
        choice = self.period_combo.currentText()
        today = date.today()
        if choice == "This Month":
            self.start_date_edit.setDate(QDate(today.year, today.month, 1))
            self.end_date_edit.setDate(QDate(today.year, today.month, today.day))
        elif choice == "Last Month":
            prev_m = 12 if today.month == 1 else today.month - 1
            prev_y = today.year - 1 if today.month == 1 else today.year
            import calendar
            _, last_d = calendar.monthrange(prev_y, prev_m)
            self.start_date_edit.setDate(QDate(prev_y, prev_m, 1))
            self.end_date_edit.setDate(QDate(prev_y, prev_m, last_d))
        elif choice == "This Year":
            self.start_date_edit.setDate(QDate(today.year, 1, 1))
            self.end_date_edit.setDate(QDate(today.year, today.month, today.day))
        elif choice == "All Time":
            self.start_date_edit.setDate(QDate(2020, 1, 1))
            self.end_date_edit.setDate(QDate(today.year, today.month, today.day))

        self.load_data()

    def get_filter_params(self):
        s = self.start_date_edit.date()
        e = self.end_date_edit.date()
        s_date = date(s.year(), s.month(), s.day())
        e_date = date(e.year(), e.month(), e.day())
        m_id = self.member_combo.currentData()
        return s_date, e_date, m_id

    def load_data(self):
        s_date, e_date, m_id = self.get_filter_params()
        report = ReportingService.get_financial_report(s_date, e_date, m_id)

        # Clear KPIs
        while self.kpi_layout.count():
            item = self.kpi_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        net = report["net_savings_paise"]
        net_col = "#10b981" if net >= 0 else "#f43f5e"
        net_prefix = "+" if net >= 0 else ""

        self._add_kpi_card("Total Income", f"₹{report['total_income_paise'] / 100:,.2f}", "#10b981")
        self._add_kpi_card("Total Expenditure", f"₹{report['total_expense_paise'] / 100:,.2f}", "#f43f5e")
        self._add_kpi_card("Net Savings Surplus", f"{net_prefix}₹{net / 100:,.2f}", net_col)
        self._add_kpi_card("Savings Rate", f"{report['savings_rate_pct']}%", "#06b6d4")

        # Category Table
        cats = report["category_breakdown"]
        self.cat_table.setRowCount(len(cats))
        for row, c in enumerate(cats):
            self.cat_table.setItem(row, 0, QTableWidgetItem(c["name"]))
            self.cat_table.setItem(row, 1, QTableWidgetItem(str(c["count"])))
            amt_it = QTableWidgetItem(f"₹{c['total_paise'] / 100:,.2f}")
            amt_it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.cat_table.setItem(row, 2, amt_it)
            share_it = QTableWidgetItem(f"{c['percentage']}%")
            share_it.setTextAlignment(Qt.AlignCenter)
            self.cat_table.setItem(row, 3, share_it)

        # Member Table
        members = report["member_attribution"]
        self.member_table.setRowCount(len(members))
        for row, m in enumerate(members):
            self.member_table.setItem(row, 0, QTableWidgetItem(m["name"]))
            self.member_table.setItem(row, 1, QTableWidgetItem(m["relation"]))

            paid_it = QTableWidgetItem(f"₹{m['paid_paise'] / 100:,.2f}")
            paid_it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.member_table.setItem(row, 2, paid_it)

            bene_it = QTableWidgetItem(f"₹{m['benefited_paise'] / 100:,.2f}")
            bene_it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.member_table.setItem(row, 3, bene_it)

            net_m = m["net_contribution_paise"]
            net_it = QTableWidgetItem(f"{'+' if net_m >= 0 else ''}₹{net_m / 100:,.2f}")
            net_it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            net_it.setForeground(Qt.green if net_m >= 0 else Qt.red)
            self.member_table.setItem(row, 4, net_it)

    def _add_kpi_card(self, title: str, value: str, val_color: str):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 14px;
            }
        """)
        lay = QVBoxLayout(card)
        lay.setSpacing(4)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600; text-transform: uppercase;")
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(f"color: {val_color}; font-size: 20px; font-weight: 700;")
        lay.addWidget(t_lbl)
        lay.addWidget(v_lbl)
        self.kpi_layout.addWidget(card)

    def export_pdf(self):
        s_date, e_date, m_id = self.get_filter_params()
        save_path_str, _ = QFileDialog.getSaveFileName(
            self, "Save Financial Statement PDF",
            f"Kanakkupulla_Statement_{date.today().strftime('%Y%m%d')}.pdf",
            "PDF Documents (*.pdf)"
        )
        if save_path_str:
            p = Path(save_path_str)
            try:
                ReportingService.export_summary_to_pdf(p, s_date, e_date, m_id)
                QMessageBox.information(self, "Export Successful", f"PDF Statement exported to:\n{p}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Could not export PDF: {str(e)}")

    def export_excel(self):
        s_date, e_date, m_id = self.get_filter_params()
        save_path_str, _ = QFileDialog.getSaveFileName(
            self, "Save Financial Workbook Excel",
            f"Kanakkupulla_Report_{date.today().strftime('%Y%m%d')}.xlsx",
            "Excel Workbooks (*.xlsx)"
        )
        if save_path_str:
            p = Path(save_path_str)
            try:
                ReportingService.export_transactions_to_excel(p, s_date, e_date, m_id)
                QMessageBox.information(self, "Export Successful", f"Excel Workbook exported to:\n{p}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Could not export Excel: {str(e)}")
