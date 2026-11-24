"""
Loans & Liabilities View:
Monitors family mortgages, auto loans, personal debt, EMI schedules,
and amortization progress.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QScrollArea, QFrame, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt
from core.loan_service import LoanService
from core.family_service import FamilyService
from config.constants import LoanStatus
from ui.loans.loan_dialog import LoanDialog, LoanPaymentDialog

class LoansView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)

        # Header bar
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Loans & EMI Liabilities")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #f8fafc;")
        sub_lbl = QLabel("Track mortgages, auto financing, personal debt, and systematic repayment amortization.")
        sub_lbl.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Member Filter
        self.member_combo = QComboBox()
        self.member_combo.addItem("All Family Liabilities", None)
        members = FamilyService.get_all_members()
        for m in members:
            self.member_combo.addItem(f"👤 {m.name}", m.id)
        self.member_combo.currentIndexChanged.connect(self.load_data)
        self.member_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 6px; padding: 6px 12px; color: #f8fafc; font-size: 13px;
            }
        """)
        header_layout.addWidget(self.member_combo)

        # Pay EMI Button
        pay_btn = QPushButton("💳 Record EMI Payment")
        pay_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981; color: white; font-weight: 600;
                padding: 8px 16px; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        pay_btn.clicked.connect(self.open_payment_dialog)
        header_layout.addWidget(pay_btn)

        # Add Loan Button
        add_btn = QPushButton("+ New Loan")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #f43f5e; color: white; font-weight: 600;
                padding: 8px 16px; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #e11d48; }
        """)
        add_btn.clicked.connect(self.open_add_dialog)
        header_layout.addWidget(add_btn)

        self.layout.addLayout(header_layout)

        # KPI Summary Cards
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(16)
        self.layout.addLayout(self.kpi_layout)

        # Scroll Area for Loan Cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(14)
        self.cards_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.cards_container)
        self.layout.addWidget(self.scroll_area)

        self.load_data()

    def open_add_dialog(self):
        dlg = LoanDialog(self)
        if dlg.exec():
            self.load_data()

    def open_payment_dialog(self, loan_id: Optional[int] = None):
        dlg = LoanPaymentDialog(preselected_loan_id=loan_id, parent=self)
        if dlg.exec():
            self.load_data()

    def load_data(self):
        # Clear KPIs
        while self.kpi_layout.count():
            item = self.kpi_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear Cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        selected_member_id = self.member_combo.currentData()
        summary = LoanService.get_loan_summary(selected_member_id)
        loans = LoanService.get_all_loans(selected_member_id)

        self._add_kpi_card("Total Borrowed", f"₹{summary['total_principal_paise'] / 100:,.2f}", "#94a3b8")
        self._add_kpi_card("Outstanding Balance", f"₹{summary['total_outstanding_paise'] / 100:,.2f}", "#f43f5e")
        self._add_kpi_card("Monthly EMI Outflow", f"₹{summary['monthly_emi_paise'] / 100:,.2f}", "#fb923c")
        self._add_kpi_card("Active Loans", str(summary['active_loans_count']), "#38bdf8")

        if not loans:
            empty_lbl = QLabel("No active loans or liabilities recorded. Your family is debt free! 🎉")
            empty_lbl.setStyleSheet("color: #64748b; font-size: 14px; padding: 40px; font-weight: 500;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(empty_lbl)
            return

        for l in loans:
            self._add_loan_card(l)

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

    def _add_loan_card(self, loan):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 16px;
            }
        """)
        lay = QVBoxLayout(card)
        lay.setSpacing(12)

        # Header Row: Name, Lender, Borrower, Status, Actions
        top_row = QHBoxLayout()
        name_lbl = QLabel(loan.loan_name)
        name_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc;")
        top_row.addWidget(name_lbl)

        lender_badge = QLabel(f"🏦 {loan.lender}")
        lender_badge.setStyleSheet("background-color: #0f172a; color: #94a3b8; padding: 4px 10px; border-radius: 6px; font-size: 11px;")
        top_row.addWidget(lender_badge)

        borrower_name = loan.family_member.name if loan.family_member else "Family"
        borrower_badge = QLabel(f"👤 {borrower_name}")
        borrower_badge.setStyleSheet("background-color: #0f172a; color: #38bdf8; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;")
        top_row.addWidget(borrower_badge)

        top_row.addStretch()

        is_active = loan.status == LoanStatus.ACTIVE.value
        status_badge = QLabel("ACTIVE" if is_active else "CLOSED")
        status_badge.setStyleSheet(
            "background-color: #1e3a8a; color: #60a5fa; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700;"
            if is_active else
            "background-color: #065f46; color: #34d399; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700;"
        )
        top_row.addWidget(status_badge)

        if is_active:
            pay_btn = QPushButton("Pay EMI")
            pay_btn.setStyleSheet("background-color: #10b981; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 600;")
            pay_btn.clicked.connect(lambda _, l_id=loan.id: self.open_payment_dialog(l_id))
            top_row.addWidget(pay_btn)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet("QPushButton { background-color: #334155; color: #94a3b8; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #ef4444; color: white; }")
        del_btn.clicked.connect(lambda _, l_id=loan.id: self.delete_loan(l_id))
        top_row.addWidget(del_btn)

        lay.addLayout(top_row)

        # Financial Details Row
        details_row = QHBoxLayout()
        p_repaid = loan.principal_amount_paise - loan.outstanding_principal_paise
        repaid_pct = (p_repaid / loan.principal_amount_paise * 100) if loan.principal_amount_paise > 0 else 100

        emi_str = f"Monthly EMI: ₹{loan.emi_amount_paise / 100:,.2f}"
        rate_str = f"Rate: {loan.interest_rate_percent}% p.a."
        due_str = f"Due: {loan.emi_due_day}th of every month"
        tenure_str = f"Tenure: {loan.tenure_months} months"

        lbl_spec = QLabel(f"{emi_str}  |  {rate_str}  |  {due_str}  |  {tenure_str}")
        lbl_spec.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 500;")
        details_row.addWidget(lbl_spec)
        details_row.addStretch()

        out_lbl = QLabel(f"Outstanding: ₹{loan.outstanding_principal_paise / 100:,.2f}")
        out_lbl.setStyleSheet("font-weight: 700; color: #f43f5e; font-size: 14px;")
        details_row.addWidget(out_lbl)
        lay.addLayout(details_row)

        # Repayment Progress bar
        bar_row = QHBoxLayout()
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(min(100, int(repaid_pct)))
        bar.setTextVisible(False)
        bar.setFixedHeight(8)
        bar.setStyleSheet("""
            QProgressBar {
                background-color: #0f172a; border: none; border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #38bdf8; border-radius: 4px;
            }
        """)
        bar_row.addWidget(bar)

        pct_repaid_lbl = QLabel(f"{repaid_pct:.1f}% Repaid")
        pct_repaid_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        bar_row.addWidget(pct_repaid_lbl)
        lay.addLayout(bar_row)

        if loan.notes:
            note_lbl = QLabel(f"Note: {loan.notes}")
            note_lbl.setStyleSheet("color: #64748b; font-size: 12px; font-style: italic;")
            lay.addWidget(note_lbl)

        self.cards_layout.addWidget(card)

    def delete_loan(self, loan_id: int):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this loan record and its payment history?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = LoanService.delete_loan(loan_id)
            if success:
                self.load_data()
            else:
                QMessageBox.critical(self, "Error", msg)
