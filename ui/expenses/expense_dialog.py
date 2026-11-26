"""
Quick Expense Entry and Full Expense Management Dialog
"""
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QDateEdit, QTextEdit, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QDate
from core.expense_service import ExpenseService
from core.category_service import CategoryService
from core.family_service import FamilyService
from core.accounting_service import AccountService
from core.attachment_service import AttachmentService
from core.financial_utils import inr_to_paise
from config.constants import ExpenseKind
from pathlib import Path
from PySide6.QtWidgets import QFileDialog

class ExpenseEntryDialog(QDialog):
    def __init__(self, expense_kind: str = ExpenseKind.DAILY.value, parent=None):
        super().__init__(parent)
        self.expense_kind = expense_kind
        self.selected_attachment_path = None
        self.setWindowTitle(f"Add {'Occasional Expense' if expense_kind == ExpenseKind.OCCASIONAL.value else 'Daily Expense'}")
        self.resize(540, 680)
        self.setMinimumSize(480, 580)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        # Title
        layout.addWidget(QLabel("Title / Item:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Petrol, Groceries, Dinner, Clothes")
        layout.addWidget(self.title_input)

        # Amount & Date row
        row1 = QHBoxLayout()
        vbox_amt = QVBoxLayout()
        vbox_amt.addWidget(QLabel("Amount (₹):"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        vbox_amt.addWidget(self.amount_input)
        row1.addLayout(vbox_amt)

        vbox_date = QVBoxLayout()
        vbox_date.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        vbox_date.addWidget(self.date_edit)
        row1.addLayout(vbox_date)
        layout.addLayout(row1)

        # If occasional expense, show Event / Project Name
        if self.expense_kind == ExpenseKind.OCCASIONAL.value:
            layout.addWidget(QLabel("Event / Project / Occasion:"))
            self.event_input = QLineEdit()
            self.event_input.setPlaceholderText("e.g. Diwali 2026, Home Renovation, Goa Trip")
            layout.addWidget(self.event_input)
        else:
            self.event_input = None

        # Category & Subcategory row
        row2 = QHBoxLayout()
        vbox_cat = QVBoxLayout()
        vbox_cat.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self.on_category_changed)
        vbox_cat.addWidget(self.category_combo)
        row2.addLayout(vbox_cat)

        vbox_subcat = QVBoxLayout()
        vbox_subcat.addWidget(QLabel("Subcategory:"))
        self.subcategory_combo = QComboBox()
        vbox_subcat.addWidget(self.subcategory_combo)
        row2.addLayout(vbox_subcat)
        layout.addLayout(row2)

        # Account & Payment Method row
        row3 = QHBoxLayout()
        vbox_acc = QVBoxLayout()
        vbox_acc.addWidget(QLabel("Paid From Account:"))
        self.account_combo = QComboBox()
        vbox_acc.addWidget(self.account_combo)
        row3.addLayout(vbox_acc)

        vbox_pm = QVBoxLayout()
        vbox_pm.addWidget(QLabel("Payment Method:"))
        self.pm_combo = QComboBox()
        self.pm_combo.addItems(["Cash", "UPI", "Debit Card", "Credit Card", "Net Banking", "Wallet", "Other"])
        vbox_pm.addWidget(self.pm_combo)
        row3.addLayout(vbox_pm)
        layout.addLayout(row3)

        # Paid By & Expense For (Beneficiary) row - Crucial Multi-User attribution
        row4 = QHBoxLayout()
        vbox_pb = QVBoxLayout()
        vbox_pb.addWidget(QLabel("Paid By (Family Member):"))
        self.paid_by_combo = QComboBox()
        vbox_pb.addWidget(self.paid_by_combo)
        row4.addLayout(vbox_pb)

        vbox_ef = QVBoxLayout()
        vbox_ef.addWidget(QLabel("Expense For (Beneficiary):"))
        self.expense_for_combo = QComboBox()
        vbox_ef.addWidget(self.expense_for_combo)
        row4.addLayout(vbox_ef)
        layout.addLayout(row4)

        # Merchant & Reference
        row5 = QHBoxLayout()
        vbox_merch = QVBoxLayout()
        vbox_merch.addWidget(QLabel("Merchant / Shop:"))
        self.merch_input = QLineEdit()
        self.merch_input.setPlaceholderText("Optional shop name")
        vbox_merch.addWidget(self.merch_input)
        row5.addLayout(vbox_merch)

        vbox_ref = QVBoxLayout()
        vbox_ref.addWidget(QLabel("Ref / UPI No:"))
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Optional transaction ID")
        vbox_ref.addWidget(self.ref_input)
        row5.addLayout(vbox_ref)
        layout.addLayout(row5)

        # Bill Image / Attachment Section
        attach_box = QHBoxLayout()
        self.attach_lbl = QLabel("No bill attached")
        self.attach_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        attach_box.addWidget(self.attach_lbl)
        attach_box.addStretch()
        attach_btn = QPushButton("📎 Attach Bill Photo")
        attach_btn.clicked.connect(self.browse_attachment)
        attach_box.addWidget(attach_btn)
        layout.addLayout(attach_box)

        layout.addSpacing(10)
        self.save_btn = QPushButton("Save Expense")
        self.save_btn.setProperty("class", "PrimaryBtn")
        self.save_btn.setFixedHeight(38)
        self.save_btn.clicked.connect(self.save)
        layout.addWidget(self.save_btn)

        self.load_dropdown_data()

    def load_dropdown_data(self):
        # 1. Categories
        categories = CategoryService.get_all_categories()
        self.category_combo.clear()
        for cat in categories:
            self.category_combo.addItem(cat.name, cat.id)

        # 2. Accounts
        accounts = AccountService.get_all_accounts()
        self.account_combo.clear()
        for acc in accounts:
            self.account_combo.addItem(f"{acc.name} ({acc.account_type})", acc.id)

        # 3. Family Members
        members = FamilyService.get_all_members()
        self.paid_by_combo.clear()
        self.expense_for_combo.clear()
        for m in members:
            self.paid_by_combo.addItem(f"{m.name} ({m.relation_type})", m.id)
            self.expense_for_combo.addItem(f"{m.name} ({m.relation_type})", m.id)

        self.on_category_changed()

    def on_category_changed(self):
        cat_id = self.category_combo.currentData()
        self.subcategory_combo.clear()
        if cat_id:
            subcats = CategoryService.get_subcategories(cat_id)
            for sub in subcats:
                self.subcategory_combo.addItem(sub.name, sub.id)

    def browse_attachment(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Attach Bill or Receipt", "", "Documents & Images (*.jpg *.jpeg *.png *.pdf *.bmp)"
        )
        if file_path:
            self.selected_attachment_path = Path(file_path)
            self.attach_lbl.setText(f"Attached: {self.selected_attachment_path.name}")

    def save(self):
        title = self.title_input.text().strip()
        amt_text = self.amount_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation", "Title is required")
            return

        try:
            amt_paise = inr_to_paise(float(amt_text))
            if amt_paise <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Validation", "Please enter a valid positive amount")
            return

        qdate = self.date_edit.date()
        txn_date = date(qdate.year(), qdate.month(), qdate.day())
        account_id = self.account_combo.currentData()
        if not account_id:
            QMessageBox.warning(self, "Validation", "Please select a payment account.")
            return

        paid_by_id = self.paid_by_combo.currentData()
        if not paid_by_id:
            QMessageBox.warning(self, "Validation", "Please select who paid for this expense.")
            return

        expense_for_id = self.expense_for_combo.currentData() or paid_by_id
        cat_id = self.category_combo.currentData()
        subcat_id = self.subcategory_combo.currentData()
        pm = self.pm_combo.currentText()
        merch = self.merch_input.text().strip() or None
        ref = self.ref_input.text().strip() or None
        event = self.event_input.text().strip() if self.event_input else None

        ok, msg, txn = ExpenseService.record_expense(
            title=title,
            amount_paise=amt_paise,
            transaction_date=txn_date,
            account_id=account_id,
            paid_by_member_id=paid_by_id,
            expense_for_member_id=expense_for_id,
            category_id=cat_id,
            subcategory_id=subcat_id,
            payment_method=pm,
            expense_kind=self.expense_kind,
            event_name=event,
            merchant=merch,
            reference_no=ref
        )

        if ok and txn:
            if self.selected_attachment_path:
                AttachmentService.attach_file_to_transaction(txn.id, self.selected_attachment_path)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", msg)
