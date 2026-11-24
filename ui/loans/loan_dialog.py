"""
Loan Dialogs:
- LoanDialog: Create loans with live EMI amortization calculation.
- LoanPaymentDialog: Pay EMI with automatic principal vs interest breakdown.
"""
from typing import Optional
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QDateEdit, QPushButton, QMessageBox, QTextEdit,
    QSpinBox, QDoubleSpinBox, QFrame
)
from PySide6.QtCore import Qt, QDate
from core.family_service import FamilyService
from core.account_service import AccountService
from core.loan_service import LoanService

class LoanDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Loan & Liability")
        self.setFixedSize(520, 640)
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; color: #f8fafc; }
            QLabel { color: #94a3b8; font-size: 13px; font-weight: 500; }
            QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 6px; padding: 8px 12px; color: #f8fafc; font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #0ea5e9;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("New Loan / Mortgage / EMI")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #f43f5e;")
        layout.addWidget(title)

        # Loan Name
        layout.addWidget(QLabel("Loan Name *"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. SBI Home Loan, Creta Car Loan")
        layout.addWidget(self.name_input)

        # Lender & Member
        row1 = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Lender / Financial Institution *"))
        self.lender_input = QLineEdit()
        self.lender_input.setPlaceholderText("e.g. State Bank of India, HDFC")
        v1.addWidget(self.lender_input)
        row1.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Borrower (Family Member)"))
        self.member_combo = QComboBox()
        self.member_combo.addItem("Family Shared Liability", None)
        members = FamilyService.get_all_members()
        for m in members:
            self.member_combo.addItem(f"👤 {m.name} ({m.relation_type})", m.id)
        v2.addWidget(self.member_combo)
        row1.addLayout(v2)
        layout.addLayout(row1)

        # Principal & Interest Rate
        row2 = QHBoxLayout()
        v3 = QVBoxLayout()
        v3.addWidget(QLabel("Principal Borrowed (₹) *"))
        self.principal_input = QLineEdit()
        self.principal_input.setPlaceholderText("e.g. 2500000")
        self.principal_input.textChanged.connect(self.update_emi_preview)
        v3.addWidget(self.principal_input)
        row2.addLayout(v3)

        v4 = QVBoxLayout()
        v4.addWidget(QLabel("Annual Interest Rate (%) *"))
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0.1, 45.0)
        self.rate_input.setValue(8.50)
        self.rate_input.setSingleStep(0.25)
        self.rate_input.valueChanged.connect(self.update_emi_preview)
        v4.addWidget(self.rate_input)
        row2.addLayout(v4)
        layout.addLayout(row2)

        # Tenure & Start Date
        row3 = QHBoxLayout()
        v5 = QVBoxLayout()
        v5.addWidget(QLabel("Tenure (Total Months) *"))
        self.tenure_input = QSpinBox()
        self.tenure_input.setRange(1, 360)
        self.tenure_input.setValue(120)
        self.tenure_input.valueChanged.connect(self.update_emi_preview)
        v5.addWidget(self.tenure_input)
        row3.addLayout(v5)

        v6 = QVBoxLayout()
        v6.addWidget(QLabel("Loan Start Date"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        today = date.today()
        self.start_date_edit.setDate(QDate(today.year, today.month, today.day))
        v6.addWidget(self.start_date_edit)
        row3.addLayout(v6)

        v7 = QVBoxLayout()
        v7.addWidget(QLabel("EMI Due Day"))
        self.due_day_spin = QSpinBox()
        self.due_day_spin.setRange(1, 31)
        self.due_day_spin.setValue(5)
        v7.addWidget(self.due_day_spin)
        row3.addLayout(v7)
        layout.addLayout(row3)

        # Live EMI Calculator Box
        self.calc_box = QFrame()
        self.calc_box.setStyleSheet("background-color: #0f172a; border-radius: 8px; padding: 12px; border: 1px solid #334155;")
        calc_lay = QVBoxLayout(self.calc_box)
        calc_lay.setSpacing(4)
        self.emi_preview_lbl = QLabel("Estimated Monthly EMI: ₹0.00")
        self.emi_preview_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8;")
        self.total_payable_lbl = QLabel("Total Repayment: ₹0.00 | Total Interest: ₹0.00")
        self.total_payable_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        calc_lay.addWidget(self.emi_preview_lbl)
        calc_lay.addWidget(self.total_payable_lbl)
        layout.addWidget(self.calc_box)

        # Notes
        layout.addWidget(QLabel("Notes (Optional)"))
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Loan account number, branch, collateral...")
        layout.addWidget(self.notes_input)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #334155; color: #f8fafc; padding: 9px 18px; border-radius: 6px;")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Add Loan")
        save_btn.setStyleSheet("background-color: #f43f5e; color: white; font-weight: 600; padding: 9px 18px; border-radius: 6px;")
        save_btn.clicked.connect(self.save)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        self.update_emi_preview()

    def update_emi_preview(self):
        try:
            p_rs = float(self.principal_input.text().strip() or "0")
            p_paise = int(round(p_rs * 100))
        except ValueError:
            p_paise = 0

        rate = self.rate_input.value()
        tenure = self.tenure_input.value()

        if p_paise > 0 and tenure > 0:
            emi_paise = LoanService.calculate_emi_paise(p_paise, rate, tenure)
            total_repay = emi_paise * tenure
            interest_paise = total_repay - p_paise
            self.emi_preview_lbl.setText(f"Estimated Monthly EMI: ₹{emi_paise / 100:,.2f}")
            self.total_payable_lbl.setText(f"Total Repay: ₹{total_repay / 100:,.0f} | Total Interest: ₹{interest_paise / 100:,.0f}")
        else:
            self.emi_preview_lbl.setText("Estimated Monthly EMI: ₹0.00")
            self.total_payable_lbl.setText("Total Repayment: ₹0.00 | Total Interest: ₹0.00")

    def save(self):
        name = self.name_input.text().strip()
        lender = self.lender_input.text().strip()
        if not name or not lender:
            QMessageBox.warning(self, "Validation Error", "Loan name and lender are required.")
            return

        try:
            p_rs = float(self.principal_input.text().strip() or "0")
            if p_rs <= 0:
                raise ValueError()
            p_paise = int(round(p_rs * 100))
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid positive principal amount.")
            return

        rate = self.rate_input.value()
        tenure = self.tenure_input.value()
        member_id = self.member_combo.currentData()
        due_day = self.due_day_spin.value()
        notes = self.notes_input.text().strip() or None

        d = self.start_date_edit.date()
        s_date = date(d.year(), d.month(), d.day())

        success, msg, _ = LoanService.create_loan(
            loan_name=name,
            lender=lender,
            principal_amount_paise=p_paise,
            interest_rate_percent=rate,
            loan_start_date=s_date,
            tenure_months=tenure,
            family_member_id=member_id,
            emi_due_day=due_day,
            notes=notes
        )

        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to create loan: {msg}")


class LoanPaymentDialog(QDialog):
    def __init__(self, preselected_loan_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record EMI Payment")
        self.setFixedSize(480, 520)
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; color: #f8fafc; }
            QLabel { color: #94a3b8; font-size: 13px; font-weight: 500; }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 6px; padding: 8px 12px; color: #f8fafc; font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus { border: 1px solid #0ea5e9; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Record EMI Repayment")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #10b981;")
        layout.addWidget(title)

        # Select Loan
        layout.addWidget(QLabel("Active Loan *"))
        self.loan_combo = QComboBox()
        self.loans = LoanService.get_all_loans()
        for l in self.loans:
            self.loan_combo.addItem(f"{l.loan_name} ({l.lender}) - Outstanding: ₹{l.outstanding_principal_paise/100:,.2f}", l.id)
            if preselected_loan_id and l.id == preselected_loan_id:
                self.loan_combo.setCurrentIndex(self.loan_combo.count() - 1)
        self.loan_combo.currentIndexChanged.connect(self.on_loan_changed)
        layout.addWidget(self.loan_combo)

        # Payment Amount
        layout.addWidget(QLabel("Payment Amount (₹) *"))
        self.amount_input = QLineEdit()
        self.amount_input.textChanged.connect(self.update_amortization_preview)
        layout.addWidget(self.amount_input)

        # Source Account
        layout.addWidget(QLabel("Payment Account *"))
        self.account_combo = QComboBox()
        accounts = AccountService.get_all_accounts()
        for a in accounts:
            self.account_combo.addItem(f"{a.name} (Bal: ₹{a.current_balance_paise/100:,.2f})", a.id)
        layout.addWidget(self.account_combo)

        # Payment Date & Mode Row
        row1 = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Payment Date"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        today = date.today()
        self.date_edit.setDate(QDate(today.year, today.month, today.day))
        v1.addWidget(self.date_edit)
        row1.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Payment Mode"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Auto Debit / ECS", "Bank Transfer", "UPI", "Cheque", "Cash"])
        v2.addWidget(self.mode_combo)
        row1.addLayout(v2)
        layout.addLayout(row1)

        # Amortization Preview Box
        self.amort_box = QFrame()
        self.amort_box.setStyleSheet("background-color: #0f172a; border-radius: 8px; padding: 10px; border: 1px solid #334155;")
        amort_lay = QVBoxLayout(self.amort_box)
        amort_lay.setSpacing(4)
        self.principal_split_lbl = QLabel("Principal Reduction: ₹0.00")
        self.principal_split_lbl.setStyleSheet("color: #10b981; font-weight: 600; font-size: 13px;")
        self.interest_split_lbl = QLabel("Interest Expense: ₹0.00")
        self.interest_split_lbl.setStyleSheet("color: #f43f5e; font-weight: 600; font-size: 13px;")
        self.new_balance_lbl = QLabel("New Outstanding Principal: ₹0.00")
        self.new_balance_lbl.setStyleSheet("color: #38bdf8; font-size: 12px;")
        amort_lay.addWidget(self.principal_split_lbl)
        amort_lay.addWidget(self.interest_split_lbl)
        amort_lay.addWidget(self.new_balance_lbl)
        layout.addWidget(self.amort_box)

        # Reference
        layout.addWidget(QLabel("Transaction Reference / UTR"))
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("e.g. UTR123456789")
        layout.addWidget(self.ref_input)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #334155; color: #f8fafc; padding: 9px 18px; border-radius: 6px;")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Confirm Payment")
        save_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: 600; padding: 9px 18px; border-radius: 6px;")
        save_btn.clicked.connect(self.save)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        self.on_loan_changed()

    def on_loan_changed(self):
        loan_id = self.loan_combo.currentData()
        target_loan = next((l for l in self.loans if l.id == loan_id), None)
        if target_loan:
            self.amount_input.setText(str(target_loan.emi_amount_paise / 100))
        self.update_amortization_preview()

    def update_amortization_preview(self):
        loan_id = self.loan_combo.currentData()
        target_loan = next((l for l in self.loans if l.id == loan_id), None)
        if not target_loan:
            return

        try:
            amt_rs = float(self.amount_input.text().strip() or "0")
            amt_paise = int(round(amt_rs * 100))
        except ValueError:
            amt_paise = 0

        monthly_rate = (target_loan.interest_rate_percent / 100.0) / 12.0
        interest_paise = int(round(target_loan.outstanding_principal_paise * monthly_rate))
        interest_paise = min(interest_paise, amt_paise)
        principal_paise = max(0, amt_paise - interest_paise)
        new_balance = max(0, target_loan.outstanding_principal_paise - principal_paise)

        self.principal_split_lbl.setText(f"Principal Reduction: ₹{principal_paise / 100:,.2f}")
        self.interest_split_lbl.setText(f"Interest Expense: ₹{interest_paise / 100:,.2f}")
        self.new_balance_lbl.setText(f"New Outstanding Principal: ₹{new_balance / 100:,.2f}")

    def save(self):
        loan_id = self.loan_combo.currentData()
        if not loan_id:
            QMessageBox.warning(self, "Validation Error", "No loan selected.")
            return

        acc_id = self.account_combo.currentData()
        if not acc_id:
            QMessageBox.warning(self, "Validation Error", "Please select a payment account.")
            return

        try:
            amt_rs = float(self.amount_input.text().strip() or "0")
            if amt_rs <= 0:
                raise ValueError()
            amt_paise = int(round(amt_rs * 100))
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid positive payment amount.")
            return

        d = self.date_edit.date()
        p_date = date(d.year(), d.month(), d.day())
        mode = self.mode_combo.currentText()
        ref = self.ref_input.text().strip() or None

        success, msg = LoanService.record_emi_payment(
            loan_id=loan_id,
            amount_paise=amt_paise,
            payment_date=p_date,
            account_id=acc_id,
            payment_method=mode,
            reference=ref
        )

        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to record payment: {msg}")
