"""
Quick Expense Entry Dialog:
Ultra-fast expense recording in < 5 seconds with preset amounts, keyboard navigation,
and instant category + account assignment for both Daily and Occasional/Other expenses.
"""
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QMessageBox, QWidget
)
from PySide6.QtCore import Qt
from core.expense_service import ExpenseService
from core.category_service import CategoryService
from core.accounting_service import AccountService
from core.family_service import FamilyService
from core.financial_utils import inr_to_paise
from config.constants import ExpenseKind

class QuickExpenseDialog(QDialog):
    def __init__(self, expense_kind: str = ExpenseKind.DAILY.value, parent=None):
        super().__init__(parent)
        self.expense_kind = expense_kind
        is_occasional = (self.expense_kind == ExpenseKind.OCCASIONAL.value)
        self.setWindowTitle(f"⚡ Quick Expense Entry - {'Occasional / Other' if is_occasional else 'Daily'}")
        self.resize(480, 580)
        self.setMinimumSize(450, 520)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        # Header
        header_wrap = QWidget()
        header_layout = QVBoxLayout(header_wrap)
        header_layout.setContentsMargins(0, 0, 0, 4)
        header_layout.setSpacing(2)

        header_title = QLabel("⚡ Quick Expense Entry")
        header_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #2dd4bf;")
        header_layout.addWidget(header_title)

        header_sub = QLabel("Record everyday out-of-pocket or occasional expenses in seconds")
        header_sub.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 500;")
        header_layout.addWidget(header_sub)
        layout.addWidget(header_wrap)

        # Expense Kind Selector Row
        kind_row = QHBoxLayout()
        kind_row.setSpacing(8)
        kind_lbl = QLabel("Expense Type:")
        kind_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #94a3b8;")
        kind_row.addWidget(kind_lbl)

        self.kind_combo = QComboBox()
        self.kind_combo.setCursor(Qt.PointingHandCursor)
        self.kind_combo.setFixedHeight(34)
        self.kind_combo.addItem("Daily Expense", ExpenseKind.DAILY.value)
        self.kind_combo.addItem("Occasional / Other Expense", ExpenseKind.OCCASIONAL.value)
        if self.expense_kind == ExpenseKind.OCCASIONAL.value:
            self.kind_combo.setCurrentIndex(1)
        else:
            self.kind_combo.setCurrentIndex(0)
        self.kind_combo.currentIndexChanged.connect(self.on_kind_changed)
        kind_row.addWidget(self.kind_combo, stretch=1)
        layout.addLayout(kind_row)

        # Optional Event/Occasion input for Occasional expenses
        self.event_wrap = QWidget()
        event_layout = QVBoxLayout(self.event_wrap)
        event_layout.setContentsMargins(0, 0, 0, 0)
        event_layout.setSpacing(3)
        event_lbl = QLabel("Event / Occasion / Project (Optional):")
        event_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #94a3b8;")
        event_layout.addWidget(event_lbl)
        self.event_input = QLineEdit()
        self.event_input.setFixedHeight(36)
        self.event_input.setPlaceholderText("e.g. Goa Trip, Diwali, Wedding, Renovation")
        event_layout.addWidget(self.event_input)
        layout.addWidget(self.event_wrap)
        self.event_wrap.setVisible(self.expense_kind == ExpenseKind.OCCASIONAL.value)

        # Amount Entry with Preset Chips
        amt_lbl = QLabel("Amount (₹) *")
        amt_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #94a3b8;")
        layout.addWidget(amt_lbl)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        self.amount_input.setFixedHeight(44)
        self.amount_input.setStyleSheet("""
            QLineEdit {
                font-size: 20px;
                font-weight: 700;
                color: #2dd4bf;
                background-color: #111827;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px 12px;
            }
            QLineEdit:focus {
                border: 1px solid #14b8a6;
                background-color: #0a0f1d;
            }
        """)
        layout.addWidget(self.amount_input)

        # Preset amount chips
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(6)
        presets = [50, 100, 200, 500, 1000, 2000, 5000]
        for p in presets:
            btn = QPushButton(f"₹{p}")
            btn.setFixedHeight(30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    color: #94a3b8;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 0 4px;
                }
                QPushButton:hover {
                    background-color: #0f766e;
                    color: #ffffff;
                    border-color: #14b8a6;
                }
            """)
            btn.clicked.connect(lambda _, val=p: self.set_amount(val))
            chips_layout.addWidget(btn)
        layout.addLayout(chips_layout)

        # Title / Description
        title_lbl = QLabel("Title / Merchant *")
        title_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #94a3b8;")
        layout.addWidget(title_lbl)

        self.title_input = QLineEdit()
        self.title_input.setFixedHeight(36)
        self.title_input.setPlaceholderText("e.g. Tea, Fuel, Vegetables, Snacks, Hotel, Shopping")
        layout.addWidget(self.title_input)

        # Category
        cat_lbl = QLabel("Category:")
        cat_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #94a3b8;")
        layout.addWidget(cat_lbl)

        self.cat_combo = QComboBox()
        self.cat_combo.setCursor(Qt.PointingHandCursor)
        self.cat_combo.setFixedHeight(36)
        for cat in CategoryService.get_all_categories():
            self.cat_combo.addItem(cat.name, cat.id)
        layout.addWidget(self.cat_combo)

        # Paid From Account
        acc_lbl = QLabel("Paid From Account *")
        acc_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #94a3b8;")
        layout.addWidget(acc_lbl)

        self.acc_combo = QComboBox()
        self.acc_combo.setCursor(Qt.PointingHandCursor)
        self.acc_combo.setFixedHeight(36)
        for acc in AccountService.get_all_accounts():
            self.acc_combo.addItem(f"{acc.name} ({acc.account_type})", acc.id)
        layout.addWidget(self.acc_combo)

        # Family Member (Payer)
        payer_lbl = QLabel("Paid By *")
        payer_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #94a3b8;")
        layout.addWidget(payer_lbl)

        self.payer_combo = QComboBox()
        self.payer_combo.setCursor(Qt.PointingHandCursor)
        self.payer_combo.setFixedHeight(36)
        for m in FamilyService.get_all_members():
            self.payer_combo.addItem(f"{m.name} ({m.relation_type})", m.id)
        layout.addWidget(self.payer_combo)

        layout.addSpacing(6)
        save_btn = QPushButton("Save Instantly (Enter)")
        save_btn.setFixedHeight(42)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f766e, stop:1 #14b8a6);
                color: #ffffff;
                font-weight: 700;
                font-size: 13px;
                border: 1px solid #2dd4bf;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #14b8a6, stop:1 #2dd4bf);
                color: #0f172a;
            }
        """)
        save_btn.clicked.connect(self.save)
        self.amount_input.returnPressed.connect(self.save)
        self.title_input.returnPressed.connect(self.save)
        layout.addWidget(save_btn)

    def on_kind_changed(self, idx: int):
        self.event_wrap.setVisible(idx == 1)

    def set_amount(self, val: int):
        self.amount_input.setText(str(val))
        self.title_input.setFocus()

    def save(self):
        title = self.title_input.text().strip()
        if not title:
            title = "Quick Expense"

        try:
            amt_text = self.amount_input.text().strip()
            if not amt_text:
                raise ValueError()
            amt_paise = inr_to_paise(float(amt_text))
            if amt_paise <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Validation", "Please enter a valid positive amount")
            return

        acc_id = self.acc_combo.currentData()
        if not acc_id:
            QMessageBox.warning(self, "Validation", "Please select a payment account.")
            return

        payer_id = self.payer_combo.currentData()
        if not payer_id:
            QMessageBox.warning(self, "Validation", "Please select who paid for this expense.")
            return

        cat_id = self.cat_combo.currentData()
        kind = self.kind_combo.currentData() or self.expense_kind
        event = self.event_input.text().strip() if (kind == ExpenseKind.OCCASIONAL.value and hasattr(self, "event_input")) else None

        ok, msg, _ = ExpenseService.record_expense(
            title=title,
            amount_paise=amt_paise,
            transaction_date=date.today(),
            account_id=acc_id,
            paid_by_member_id=payer_id,
            expense_for_member_id=payer_id,
            category_id=cat_id,
            payment_method="Cash / UPI",
            expense_kind=kind,
            event_name=event
        )
        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to record expense: {msg}")
