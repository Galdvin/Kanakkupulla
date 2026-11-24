"""
Recurring Rule Dialog:
Configure automated scheduling for recurring expenses and income.
"""
from typing import Optional
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QDateEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from core.family_service import FamilyService
from core.account_service import AccountService
from core.category_service import CategoryService
from core.recurring_service import RecurringService
from config.constants import TransactionType

FREQUENCIES = ["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"]

class RecurringRuleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Schedule Recurring Transaction")
        self.setFixedSize(500, 580)
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; color: #f8fafc; }
            QLabel { color: #94a3b8; font-size: 13px; font-weight: 500; }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 6px; padding: 8px 12px; color: #f8fafc; font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #0ea5e9;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("New Recurring Rule")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(title)

        # Title / Description
        layout.addWidget(QLabel("Rule Title *"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. House Rent, WiFi Internet, Monthly Salary")
        layout.addWidget(self.title_input)

        # Type & Frequency Row
        row1 = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Transaction Type *"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([TransactionType.EXPENSE.value, TransactionType.INCOME.value])
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        v1.addWidget(self.type_combo)
        row1.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Recurrence Frequency *"))
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(FREQUENCIES)
        self.freq_combo.setCurrentText("Monthly")
        v2.addWidget(self.freq_combo)
        row1.addLayout(v2)
        layout.addLayout(row1)

        # Amount & Account Row
        row2 = QHBoxLayout()
        v3 = QVBoxLayout()
        v3.addWidget(QLabel("Amount (₹) *"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("e.g. 15000")
        v3.addWidget(self.amount_input)
        row2.addLayout(v3)

        v4 = QVBoxLayout()
        v4.addWidget(QLabel("Primary Account *"))
        self.account_combo = QComboBox()
        accounts = AccountService.get_all_accounts()
        for a in accounts:
            self.account_combo.addItem(f"{a.name} (Bal: ₹{a.current_balance_paise/100:,.2f})", a.id)
        v4.addWidget(self.account_combo)
        row2.addLayout(v4)
        layout.addLayout(row2)

        # Category & Member Row
        row3 = QHBoxLayout()
        v5 = QVBoxLayout()
        v5.addWidget(QLabel("Category *"))
        self.cat_combo = QComboBox()
        v5.addWidget(self.cat_combo)
        row3.addLayout(v5)

        v6 = QVBoxLayout()
        v6.addWidget(QLabel("Family Member *"))
        self.member_combo = QComboBox()
        members = FamilyService.get_all_members()
        for m in members:
            self.member_combo.addItem(f"👤 {m.name} ({m.relation_type})", m.id)
        v6.addWidget(self.member_combo)
        row3.addLayout(v6)
        layout.addLayout(row3)

        # Dates Row (Start Date & Optional End Date)
        row4 = QHBoxLayout()
        v7 = QVBoxLayout()
        v7.addWidget(QLabel("Start Date (First Due Date) *"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        today = date.today()
        self.start_date_edit.setDate(QDate(today.year, today.month, today.day))
        v7.addWidget(self.start_date_edit)
        row4.addLayout(v7)

        v8 = QVBoxLayout()
        v8.addWidget(QLabel("End Date (Optional)"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate(today.year + 1, today.month, today.day))
        v8.addWidget(self.end_date_edit)
        row4.addLayout(v8)
        layout.addLayout(row4)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #334155; color: #f8fafc; padding: 9px 18px; border-radius: 6px;")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Rule")
        save_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: 600; padding: 9px 18px; border-radius: 6px;")
        save_btn.clicked.connect(self.save)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        self.on_type_changed()

    def on_type_changed(self):
        txn_type = self.type_combo.currentText()
        self.cat_combo.clear()
        categories = CategoryService.get_categories_by_type(txn_type)
        for c in categories:
            self.cat_combo.addItem(c.name, c.id)

    def save(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation Error", "Rule title cannot be empty.")
            return

        try:
            amt_rs = float(self.amount_input.text().strip() or "0")
            if amt_rs <= 0:
                raise ValueError()
            amt_paise = int(round(amt_rs * 100))
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid positive amount.")
            return

        acc_id = self.account_combo.currentData()
        member_id = self.member_combo.currentData()
        cat_id = self.cat_combo.currentData()

        if not acc_id or not member_id:
            QMessageBox.warning(self, "Validation Error", "Account and Family Member are required.")
            return

        t_type = self.type_combo.currentText()
        freq = self.freq_combo.currentText()

        s_q = self.start_date_edit.date()
        start_d = date(s_q.year(), s_q.month(), s_q.day())

        e_q = self.end_date_edit.date()
        end_d = date(e_q.year(), e_q.month(), e_q.day())

        success, msg, _ = RecurringService.create_rule(
            title=title,
            transaction_type=t_type,
            amount_paise=amt_paise,
            frequency=freq,
            start_date=start_d,
            account_id=acc_id,
            paid_by_member_id=member_id,
            category_id=cat_id,
            end_date=end_d
        )

        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to create rule: {msg}")
