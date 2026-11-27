"""
Quick Expense Entry Dialog:
Ultra-fast expense recording with preset amounts, keyboard navigation,
clean 2-column cell display, and instant category + account assignment.
"""
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QMessageBox, QWidget, QFrame
)
from PySide6.QtCore import Qt
from core.expense_service import ExpenseService
from core.category_service import CategoryService
from core.accounting_service import AccountService
from core.family_service import FamilyService
from core.financial_utils import inr_to_paise
from config.constants import ExpenseKind

FIELD_LABEL_STYLE = "font-size: 12px; font-weight: 600; color: #94a3b8; margin-bottom: 2px;"

INPUT_STYLE = """
    QLineEdit, QComboBox {
        background-color: #111827;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 13px;
        min-height: 22px;
    }
    QLineEdit:focus, QComboBox:focus {
        border: 1px solid #14b8a6;
        background-color: #0b1120;
    }
    QComboBox::drop-down {
        border: none;
        width: 20px;
    }
"""

class QuickExpenseDialog(QDialog):
    def __init__(self, expense_kind: str = ExpenseKind.DAILY.value, parent=None):
        super().__init__(parent)
        self.expense_kind = expense_kind
        is_occasional = (self.expense_kind == ExpenseKind.OCCASIONAL.value)
        self.setWindowTitle(f"⚡ Quick Expense Entry - {'Occasional / Other' if is_occasional else 'Daily'}")
        self.resize(540, 560)
        self.setMinimumSize(500, 520)
        self.setStyleSheet(INPUT_STYLE)
        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(12)
        root_layout.setContentsMargins(24, 20, 24, 20)

        # Header
        header_wrap = QWidget()
        header_layout = QVBoxLayout(header_wrap)
        header_layout.setContentsMargins(0, 0, 0, 2)
        header_layout.setSpacing(2)

        header_title = QLabel("⚡ Quick Expense Entry")
        header_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #2dd4bf;")
        header_layout.addWidget(header_title)

        header_sub = QLabel("Record everyday out-of-pocket or occasional expenses in seconds")
        header_sub.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 500;")
        header_layout.addWidget(header_sub)
        root_layout.addWidget(header_wrap)

        # Row 1: Expense Classification (2 Columns)
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        col_type = QVBoxLayout()
        col_type.setSpacing(4)
        lbl_type = QLabel("Expense Type:")
        lbl_type.setStyleSheet(FIELD_LABEL_STYLE)
        col_type.addWidget(lbl_type)
        self.kind_combo = QComboBox()
        self.kind_combo.setFixedHeight(38)
        self.kind_combo.setCursor(Qt.PointingHandCursor)
        self.kind_combo.addItem("Daily Expense", ExpenseKind.DAILY.value)
        self.kind_combo.addItem("Occasional / Other Expense", ExpenseKind.OCCASIONAL.value)
        if self.expense_kind == ExpenseKind.OCCASIONAL.value:
            self.kind_combo.setCurrentIndex(1)
        else:
            self.kind_combo.setCurrentIndex(0)
        self.kind_combo.currentIndexChanged.connect(self.on_kind_changed)
        col_type.addWidget(self.kind_combo)
        row1.addLayout(col_type, stretch=1)

        col_event = QVBoxLayout()
        col_event.setSpacing(4)
        self.event_lbl = QLabel("Event / Occasion (Optional):")
        self.event_lbl.setStyleSheet(FIELD_LABEL_STYLE)
        col_event.addWidget(self.event_lbl)
        self.event_input = QLineEdit()
        self.event_input.setFixedHeight(38)
        self.event_input.setPlaceholderText("e.g. Goa Trip, Diwali, Wedding")
        col_event.addWidget(self.event_input)
        row1.addLayout(col_event, stretch=1)

        root_layout.addLayout(row1)

        # Row 2: Amount Hero Cell
        amt_wrap = QVBoxLayout()
        amt_wrap.setSpacing(4)
        amt_lbl = QLabel("Amount (₹) *")
        amt_lbl.setStyleSheet(FIELD_LABEL_STYLE)
        amt_wrap.addWidget(amt_lbl)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        self.amount_input.setFixedHeight(46)
        self.amount_input.setStyleSheet("""
            QLineEdit {
                font-size: 22px;
                font-weight: 700;
                color: #2dd4bf;
                background-color: #111827;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px 14px;
            }
            QLineEdit:focus {
                border: 1px solid #14b8a6;
                background-color: #0b1120;
            }
        """)
        amt_wrap.addWidget(self.amount_input)
        root_layout.addLayout(amt_wrap)

        # Row 3: Preset Amount Quick Chips
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(6)
        presets = [50, 100, 200, 500, 1000, 2000, 5000]
        for p in presets:
            btn = QPushButton(f"₹{p:,}")
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
        root_layout.addLayout(chips_layout)

        # Row 4: Title / Merchant Description
        title_wrap = QVBoxLayout()
        title_wrap.setSpacing(4)
        title_lbl = QLabel("Title / Merchant *")
        title_lbl.setStyleSheet(FIELD_LABEL_STYLE)
        title_wrap.addWidget(title_lbl)

        self.title_input = QLineEdit()
        self.title_input.setFixedHeight(38)
        self.title_input.setPlaceholderText("e.g. Tea, Fuel, Vegetables, Snacks, Hotel, Hand Loan")
        title_wrap.addWidget(self.title_input)
        root_layout.addLayout(title_wrap)

        # Row 5: Category & Account (2 Columns)
        row5 = QHBoxLayout()
        row5.setSpacing(12)

        col_cat = QVBoxLayout()
        col_cat.setSpacing(4)
        cat_lbl = QLabel("Category *")
        cat_lbl.setStyleSheet(FIELD_LABEL_STYLE)
        col_cat.addWidget(cat_lbl)
        self.cat_combo = QComboBox()
        self.cat_combo.setCursor(Qt.PointingHandCursor)
        self.cat_combo.setFixedHeight(38)
        for cat in CategoryService.get_all_categories():
            self.cat_combo.addItem(cat.name, cat.id)
        col_cat.addWidget(self.cat_combo)
        row5.addLayout(col_cat, stretch=1)

        col_acc = QVBoxLayout()
        col_acc.setSpacing(4)
        acc_lbl = QLabel("Paid From Account *")
        acc_lbl.setStyleSheet(FIELD_LABEL_STYLE)
        col_acc.addWidget(acc_lbl)
        self.acc_combo = QComboBox()
        self.acc_combo.setCursor(Qt.PointingHandCursor)
        self.acc_combo.setFixedHeight(38)
        for acc in AccountService.get_all_accounts():
            self.acc_combo.addItem(f"{acc.name} ({acc.account_type})", acc.id)
        col_acc.addWidget(self.acc_combo)
        row5.addLayout(col_acc, stretch=1)

        root_layout.addLayout(row5)

        # Row 6: Paid By & Payment Method (2 Columns)
        row6 = QHBoxLayout()
        row6.setSpacing(12)

        col_payer = QVBoxLayout()
        col_payer.setSpacing(4)
        payer_lbl = QLabel("Paid By *")
        payer_lbl.setStyleSheet(FIELD_LABEL_STYLE)
        col_payer.addWidget(payer_lbl)
        self.payer_combo = QComboBox()
        self.payer_combo.setCursor(Qt.PointingHandCursor)
        self.payer_combo.setFixedHeight(38)
        for m in FamilyService.get_all_members():
            self.payer_combo.addItem(f"{m.name} ({m.relation_type})", m.id)
        col_payer.addWidget(self.payer_combo)
        row6.addLayout(col_payer, stretch=1)

        col_pm = QVBoxLayout()
        col_pm.setSpacing(4)
        pm_lbl = QLabel("Payment Method")
        pm_lbl.setStyleSheet(FIELD_LABEL_STYLE)
        col_pm.addWidget(pm_lbl)
        self.pm_combo = QComboBox()
        self.pm_combo.setCursor(Qt.PointingHandCursor)
        self.pm_combo.setFixedHeight(38)
        self.pm_combo.addItems(["Cash", "UPI", "Debit Card", "Credit Card", "Net Banking", "Wallet", "Other"])
        col_pm.addWidget(self.pm_combo)
        row6.addLayout(col_pm, stretch=1)

        root_layout.addLayout(row6)

        # Save Button
        root_layout.addSpacing(4)
        save_btn = QPushButton("Save Instantly (Enter)")
        save_btn.setFixedHeight(44)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f766e, stop:1 #14b8a6);
                color: #ffffff;
                font-weight: 700;
                font-size: 14px;
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
        root_layout.addWidget(save_btn)

        # Initial state for event input
        self.on_kind_changed(self.kind_combo.currentIndex())

    def on_kind_changed(self, idx: int):
        is_occasional = (idx == 1)
        self.event_input.setEnabled(is_occasional)
        if is_occasional:
            self.event_lbl.setText("Event / Occasion (Optional):")
            self.event_input.setPlaceholderText("e.g. Goa Trip, Diwali, Wedding")
            self.event_input.setStyleSheet("background-color: #111827; color: #f8fafc;")
        else:
            self.event_lbl.setText("Event / Occasion:")
            self.event_input.setPlaceholderText("Regular daily living expense")
            self.event_input.setStyleSheet("background-color: #0f172a; color: #475569;")

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
        pm = self.pm_combo.currentText()
        event = self.event_input.text().strip() if (kind == ExpenseKind.OCCASIONAL.value and hasattr(self, "event_input")) else None

        ok, msg, _ = ExpenseService.record_expense(
            title=title,
            amount_paise=amt_paise,
            transaction_date=date.today(),
            account_id=acc_id,
            paid_by_member_id=payer_id,
            expense_for_member_id=payer_id,
            category_id=cat_id,
            payment_method=pm,
            expense_kind=kind,
            event_name=event
        )
        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to record expense: {msg}")
