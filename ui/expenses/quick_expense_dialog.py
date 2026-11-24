"""
Quick Expense Entry Dialog:
Ultra-fast expense recording in < 5 seconds with preset amounts, keyboard navigation,
and instant category + account assignment.
"""
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QMessageBox, QFrame, QButtonGroup
)
from PySide6.QtCore import Qt
from core.expense_service import ExpenseService
from core.category_service import CategoryService
from core.accounting_service import AccountService
from core.family_service import FamilyService
from core.financial_utils import inr_to_paise

class QuickExpenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚡ Quick Expense Entry (< 5 sec)")
        self.setFixedSize(420, 460)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        # Amount Entry with Preset Chips
        layout.addWidget(QLabel("Amount (₹):"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        self.amount_input.setStyleSheet("font-size: 20px; font-weight: 800; color: #14b8a6;")
        layout.addWidget(self.amount_input)

        chips_layout = QHBoxLayout()
        presets = [50, 100, 200, 500, 1000, 2000]
        for p in presets:
            btn = QPushButton(f"₹{p}")
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda _, val=p: self.set_amount(val))
            chips_layout.addWidget(btn)
        layout.addLayout(chips_layout)

        # Title / Description
        layout.addWidget(QLabel("Title / Merchant:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Tea, Fuel, Vegetables, Snacks")
        layout.addWidget(self.title_input)

        # Category
        layout.addWidget(QLabel("Category:"))
        self.cat_combo = QComboBox()
        for cat in CategoryService.get_all_categories():
            self.cat_combo.addItem(cat.name, cat.id)
        layout.addWidget(self.cat_combo)

        # Paid From Account
        layout.addWidget(QLabel("Paid From Account:"))
        self.acc_combo = QComboBox()
        for acc in AccountService.get_all_accounts():
            self.acc_combo.addItem(f"{acc.name} ({acc.account_type})", acc.id)
        layout.addWidget(self.acc_combo)

        # Family Member (Payer)
        layout.addWidget(QLabel("Paid By:"))
        self.payer_combo = QComboBox()
        for m in FamilyService.get_all_members():
            self.payer_combo.addItem(f"{m.name} ({m.relation_type})", m.id)
        layout.addWidget(self.payer_combo)

        layout.addSpacing(10)
        save_btn = QPushButton("Save Instantly (Enter)")
        save_btn.setProperty("class", "PrimaryBtn")
        save_btn.setFixedHeight(40)
        save_btn.clicked.connect(self.save)
        self.amount_input.returnPressed.connect(self.save)
        self.title_input.returnPressed.connect(self.save)
        layout.addWidget(save_btn)

    def set_amount(self, val: int):
        self.amount_input.setText(str(val))
        self.title_input.setFocus()

    def save(self):
        title = self.title_input.text().strip() or "Quick Expense"
        try:
            amt_paise = inr_to_paise(float(self.amount_input.text().strip()))
            if amt_paise <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Validation", "Please enter a valid amount")
            return

        acc_id = self.acc_combo.currentData()
        payer_id = self.payer_combo.currentData()
        cat_id = self.cat_combo.currentData()

        ok, msg, _ = ExpenseService.record_expense(
            title=title,
            amount_paise=amt_paise,
            transaction_date=date.today(),
            account_id=acc_id,
            paid_by_member_id=payer_id,
            expense_for_member_id=payer_id,
            category_id=cat_id,
            payment_method="Cash / UPI"
        )
        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", msg)
