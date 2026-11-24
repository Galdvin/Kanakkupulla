"""
Smart Receipt Scanner Dialog:
Upload an image of a bill/receipt, automatically extract merchant, date, amount, category,
and allow user review before one-click entry into Daily Expenses.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QComboBox, QMessageBox, QDateEdit, QFrame
)
from PySide6.QtCore import Qt, QDate
from core.ocr_scanner_service import SmartReceiptScanner
from core.expense_service import ExpenseService
from core.category_service import CategoryService
from core.accounting_service import AccountService
from core.user_service import UserService
from core.financial_utils import inr_to_paise, format_inr
from config.constants import ExpenseKind

class SmartReceiptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Smart Receipt Scanner")
        self.setFixedSize(480, 520)
        self.scanned_file_path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        # Upload header card
        drop_card = QFrame()
        drop_card.setProperty("class", "Card")
        drop_layout = QVBoxLayout(drop_card)
        drop_layout.setAlignment(Qt.AlignCenter)

        upload_title = QLabel("Select or Drag Receipt Photograph")
        upload_title.setStyleSheet("font-weight: 700; color: #38bdf8;")
        drop_layout.addWidget(upload_title)

        self.file_lbl = QLabel("No image selected")
        self.file_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        drop_layout.addWidget(self.file_lbl)

        choose_btn = QPushButton("Browse Image (.jpg, .png, .pdf)")
        choose_btn.clicked.connect(self.browse_image)
        drop_layout.addWidget(choose_btn)

        layout.addWidget(drop_card)

        # Extracted fields review
        layout.addWidget(QLabel("Extracted Merchant / Store:"))
        self.merchant_input = QLineEdit()
        layout.addWidget(self.merchant_input)

        row1 = QHBoxLayout()
        vbox_amt = QVBoxLayout()
        vbox_amt.addWidget(QLabel("Extracted Total (₹):"))
        self.amount_input = QLineEdit()
        vbox_amt.addWidget(self.amount_input)
        row1.addLayout(vbox_amt)

        vbox_date = QVBoxLayout()
        vbox_date.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        vbox_date.addWidget(self.date_edit)
        row1.addLayout(vbox_date)
        layout.addLayout(row1)

        layout.addWidget(QLabel("Category:"))
        self.cat_combo = QComboBox()
        for cat in CategoryService.get_all_categories():
            self.cat_combo.addItem(cat.name, cat.id)
        layout.addWidget(self.cat_combo)

        layout.addWidget(QLabel("Paid From Account:"))
        self.acc_combo = QComboBox()
        for acc in AccountService.get_all_accounts():
            self.acc_combo.addItem(acc.name, acc.id)
        layout.addWidget(self.acc_combo)

        layout.addSpacing(10)
        self.confirm_btn = QPushButton("Confirm & Save Expense")
        self.confirm_btn.setProperty("class", "SuccessBtn")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.save_extracted_expense)
        layout.addWidget(self.confirm_btn)

    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Receipt Image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.scanned_file_path = Path(file_path)
            self.file_lbl.setText(self.scanned_file_path.name)
            
            # Run parser
            parsed = SmartReceiptScanner.parse_bill_image(self.scanned_file_path)
            self.merchant_input.setText(parsed["detected_merchant"])
            self.amount_input.setText(f"{parsed['detected_amount_paise']/100:.2f}")
            self.date_edit.setDate(QDate(parsed["detected_date"].year, parsed["detected_date"].month, parsed["detected_date"].day))
            
            # Match category
            cat_name = parsed["detected_category"]
            idx = self.cat_combo.findText(cat_name)
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)

            self.confirm_btn.setEnabled(True)

    def save_extracted_expense(self):
        merchant = self.merchant_input.text().strip() or "Scanned Expense"
        try:
            amt_paise = inr_to_paise(float(self.amount_input.text().strip()))
            if amt_paise <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Validation", "Invalid amount")
            return

        qdate = self.date_edit.date()
        from datetime import date
        txn_date = date(qdate.year(), qdate.month(), qdate.day())
        account_id = self.acc_combo.currentData()
        category_id = self.cat_combo.currentData()
        user = UserService.get_all_users()[0]

        ok, msg, _ = ExpenseService.record_expense(
            title=f"Bill - {merchant}",
            amount_paise=amt_paise,
            transaction_date=txn_date,
            account_id=account_id,
            paid_by_id=user.id,
            expense_for_id=user.id,
            category_id=category_id,
            merchant=merchant,
            expense_kind=ExpenseKind.DAILY.value,
            payment_method="UPI"
        )
        if ok:
            QMessageBox.information(self, "Success", "Scanned expense recorded successfully!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", msg)
