"""
Smart Receipt OCR Review Dialog:
Allows uploading receipt photos, reviews AI/OCR extracted data,
and saves the transaction with receipt attachment in one click.
"""
from typing import Optional
from pathlib import Path
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QDateEdit, QPushButton, QMessageBox, QFileDialog,
    QFrame, QSplitter
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QDate

from core.ocr_scanner_service import SmartReceiptScanner
from core.expense_service import ExpenseService
from core.attachment_service import AttachmentService
from core.family_service import FamilyService
from core.account_service import AccountService
from core.category_service import CategoryService

class SmartReceiptReviewDialog(QDialog):
    def __init__(self, initial_image_path: Optional[Path] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Smart Receipt Scanner & Pre-fill")
        self.setFixedSize(840, 620)
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; color: #f8fafc; }
            QLabel { color: #94a3b8; font-size: 13px; font-weight: 500; }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 6px; padding: 8px 12px; color: #f8fafc; font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus { border: 1px solid #0ea5e9; }
        """)

        self.current_image_path: Optional[Path] = initial_image_path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        top_bar = QHBoxLayout()
        t_box = QVBoxLayout()
        title_lbl = QLabel("Smart Receipt Scanner (OCR)")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #38bdf8;")
        sub_lbl = QLabel("Scan or upload a bill image. Review extracted fields before saving to financial ledger.")
        sub_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        t_box.addWidget(title_lbl)
        t_box.addWidget(sub_lbl)
        top_bar.addLayout(t_box)
        top_bar.addStretch()

        choose_btn = QPushButton("📁 Select Bill Image")
        choose_btn.setStyleSheet("background-color: #0284c7; color: white; padding: 8px 14px; border-radius: 6px; font-weight: 600;")
        choose_btn.clicked.connect(self.choose_file)
        top_bar.addWidget(choose_btn)
        layout.addLayout(top_bar)

        # Splitter: Left Preview, Right Form
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #334155; width: 2px; }")

        # Left: Image Preview Box
        preview_box = QFrame()
        preview_box.setStyleSheet("background-color: #1e293b; border-radius: 8px; border: 1px solid #334155;")
        p_lay = QVBoxLayout(preview_box)
        p_lay.setAlignment(Qt.AlignCenter)
        self.image_preview_lbl = QLabel("No Receipt Selected\n\nClick 'Select Bill Image' to upload")
        self.image_preview_lbl.setAlignment(Qt.AlignCenter)
        self.image_preview_lbl.setStyleSheet("color: #64748b; font-size: 13px;")
        self.image_preview_lbl.setFixedSize(360, 440)
        self.image_preview_lbl.setScaledContents(True)
        p_lay.addWidget(self.image_preview_lbl)
        splitter.addWidget(preview_box)

        # Right: Extracted Fields Form
        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #1e293b; border-radius: 8px; border: 1px solid #334155; padding: 14px;")
        f_lay = QVBoxLayout(form_frame)
        f_lay.setSpacing(10)

        f_lay.addWidget(QLabel("Merchant / Store Name *"))
        self.merchant_input = QLineEdit()
        self.merchant_input.setPlaceholderText("e.g. DMart, Shell Station")
        f_lay.addWidget(self.merchant_input)

        row1 = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Amount (₹) *"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("e.g. 2500")
        v1.addWidget(self.amount_input)
        row1.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Bill Date *"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        v2.addWidget(self.date_edit)
        row1.addLayout(v2)
        f_lay.addLayout(row1)

        row2 = QHBoxLayout()
        v3 = QVBoxLayout()
        v3.addWidget(QLabel("Expense Category *"))
        self.cat_combo = QComboBox()
        categories = CategoryService.get_categories_by_type("Expense")
        for c in categories:
            self.cat_combo.addItem(c.name, c.id)
        v3.addWidget(self.cat_combo)
        row2.addLayout(v3)

        v4 = QVBoxLayout()
        v4.addWidget(QLabel("Payment Account *"))
        self.account_combo = QComboBox()
        accounts = AccountService.get_all_accounts()
        for a in accounts:
            self.account_combo.addItem(f"{a.name}", a.id)
        v4.addWidget(self.account_combo)
        row2.addLayout(v4)
        f_lay.addLayout(row2)

        row3 = QHBoxLayout()
        v5 = QVBoxLayout()
        v5.addWidget(QLabel("Paid By Member *"))
        self.payer_combo = QComboBox()
        members = FamilyService.get_all_members()
        for m in members:
            self.payer_combo.addItem(f"👤 {m.name}", m.id)
        v5.addWidget(self.payer_combo)
        row3.addLayout(v5)

        v6 = QVBoxLayout()
        v6.addWidget(QLabel("Expense For Member *"))
        self.beneficiary_combo = QComboBox()
        for m in members:
            self.beneficiary_combo.addItem(f"👤 {m.name}", m.id)
        v6.addWidget(self.beneficiary_combo)
        row3.addLayout(v6)
        f_lay.addLayout(row3)

        f_lay.addWidget(QLabel("Payment Method"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["UPI / QR", "Credit Card", "Debit Card", "Cash", "Net Banking"])
        f_lay.addWidget(self.mode_combo)

        # Confidence status
        self.status_lbl = QLabel("Status: Ready to scan")
        self.status_lbl.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 600;")
        f_lay.addWidget(self.status_lbl)

        # Buttons
        btn_box = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #334155; color: #f8fafc; padding: 8px 16px; border-radius: 6px;")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("✓ Confirm & Record Expense")
        save_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: 600; padding: 8px 18px; border-radius: 6px;")
        save_btn.clicked.connect(self.save_and_attach)

        btn_box.addStretch()
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)
        f_lay.addLayout(btn_box)

        splitter.addWidget(form_frame)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)
        layout.addWidget(splitter)

        if self.current_image_path:
            self.process_image(self.current_image_path)

    def choose_file(self):
        file_path_str, _ = QFileDialog.getOpenFileName(
            self, "Select Receipt Image", "",
            "Receipt Images (*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.pdf)"
        )
        if file_path_str:
            p = Path(file_path_str)
            self.current_image_path = p
            self.process_image(p)

    def process_image(self, p: Path):
        # 1. Show preview
        pix = QPixmap(str(p))
        if not pix.isNull():
            self.image_preview_lbl.setPixmap(pix.scaled(340, 420, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.image_preview_lbl.setText(f"Loaded: {p.name}")

        # 2. Run OCR / heuristic extraction
        parsed = SmartReceiptScanner.parse_bill_image(p)

        self.merchant_input.setText(parsed["detected_merchant"])
        self.amount_input.setText(str(parsed["detected_amount_paise"] / 100.0))

        d = parsed["detected_date"]
        self.date_edit.setDate(QDate(d.year, d.month, d.day))

        # Suggest matching category
        cat_hint = parsed["detected_category"]
        for idx in range(self.cat_combo.count()):
            if cat_hint.lower() in self.cat_combo.itemText(idx).lower():
                self.cat_combo.setCurrentIndex(idx)
                break

        conf = int(parsed["confidence_score"] * 100)
        self.status_lbl.setText(f"OCR Confidence: {conf}%  |  Detected: {parsed['detected_merchant']}")

    def save_and_attach(self):
        merchant = self.merchant_input.text().strip()
        if not merchant:
            QMessageBox.warning(self, "Validation Error", "Merchant / Store name is required.")
            return

        try:
            amt_rs = float(self.amount_input.text().strip() or "0")
            if amt_rs <= 0:
                raise ValueError()
            amt_paise = int(round(amt_rs * 100))
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid positive amount.")
            return

        q_d = self.date_edit.date()
        t_date = date(q_d.year(), q_d.month(), q_d.day())

        cat_id = self.cat_combo.currentData()
        acc_id = self.account_combo.currentData()
        payer_id = self.payer_combo.currentData()
        bene_id = self.beneficiary_combo.currentData()
        mode = self.mode_combo.currentText()

        # 1. Record Expense
        ok, msg, txn = ExpenseService.record_expense(
            title=f"Purchase at {merchant}",
            amount_paise=amt_paise,
            transaction_date=t_date,
            account_id=acc_id,
            category_id=cat_id,
            paid_by_member_id=payer_id,
            expense_for_member_id=bene_id,
            payment_method=mode,
            merchant=merchant,
            expense_kind="Daily"
        )

        if not ok or not txn:
            QMessageBox.critical(self, "Error", f"Failed to record expense: {msg}")
            return

        # 2. Attach receipt image if present
        if self.current_image_path and self.current_image_path.exists():
            AttachmentService.save_attachment(txn.id, self.current_image_path)

        QMessageBox.information(self, "Success", "Expense successfully recorded and receipt attached to permanent storage!")
        self.accept()
