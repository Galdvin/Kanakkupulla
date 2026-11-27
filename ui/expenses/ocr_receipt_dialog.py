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
    QFrame, QSplitter, QScrollArea, QGridLayout, QWidget
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
        self.resize(980, 700)
        self.setMinimumSize(880, 640)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b1120;
                color: #f8fafc;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 0px 12px;
                color: #f8fafc;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #00d2aa;
                background-color: #162032;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #f8fafc;
                selection-background-color: #00d2aa;
                selection-color: #0b1120;
                border: 1px solid #334155;
            }
        """)

        self.current_image_path: Optional[Path] = initial_image_path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        top_bar = QHBoxLayout()
        t_box = QVBoxLayout()
        t_box.setSpacing(4)
        title_lbl = QLabel("Smart Receipt Scanner (OCR)")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #38bdf8;")
        sub_lbl = QLabel("Scan or upload a bill image. Review extracted fields before saving to financial ledger.")
        sub_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        t_box.addWidget(title_lbl)
        t_box.addWidget(sub_lbl)
        top_bar.addLayout(t_box)
        top_bar.addStretch()

        choose_btn = QPushButton("📁 Select Bill Image")
        choose_btn.setFixedHeight(36)
        choose_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; color: white; padding: 0 16px;
                border-radius: 6px; font-weight: 600; font-size: 13px; border: none;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        choose_btn.clicked.connect(self.choose_file)
        top_bar.addWidget(choose_btn)
        layout.addLayout(top_bar)

        # Splitter: Left Preview, Right Form
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #1e293b;
                width: 3px;
                margin: 0px 4px;
            }
        """)

        # Left: Image Preview Box
        preview_box = QFrame()
        preview_box.setObjectName("previewBox")
        preview_box.setStyleSheet("""
            QFrame#previewBox {
                background-color: #1e293b;
                border-radius: 10px;
                border: 1px solid #334155;
            }
        """)
        p_lay = QVBoxLayout(preview_box)
        p_lay.setContentsMargins(16, 16, 16, 16)
        p_lay.setSpacing(12)

        prev_header = QLabel("RECEIPT PREVIEW")
        prev_header.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        p_lay.addWidget(prev_header)

        preview_scroll = QScrollArea()
        preview_scroll.setWidgetResizable(True)
        preview_scroll.setFrameShape(QFrame.NoFrame)
        preview_scroll.setStyleSheet("background-color: #0f172a; border-radius: 8px; border: 1px dashed #334155;")

        self.image_preview_lbl = QLabel("No Receipt Selected\n\nClick 'Select Bill Image' above\nor browse below to scan")
        self.image_preview_lbl.setAlignment(Qt.AlignCenter)
        self.image_preview_lbl.setStyleSheet("color: #64748b; font-size: 13px; background: transparent; padding: 20px;")
        self.image_preview_lbl.setMinimumSize(280, 360)
        preview_scroll.setWidget(self.image_preview_lbl)
        p_lay.addWidget(preview_scroll, stretch=1)

        browse_btn = QPushButton("📂 Browse / Replace Image")
        browse_btn.setFixedHeight(36)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155; color: #f8fafc; border-radius: 6px;
                font-weight: 600; font-size: 12px; border: none;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        browse_btn.clicked.connect(self.choose_file)
        p_lay.addWidget(browse_btn)

        splitter.addWidget(preview_box)

        # Right: Extracted Fields Form (wrapped in QScrollArea so fields NEVER squash or merge)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        form_frame = QFrame()
        form_frame.setObjectName("formFrame")
        form_frame.setStyleSheet("""
            QFrame#formFrame {
                background-color: #1e293b;
                border-radius: 10px;
                border: 1px solid #334155;
            }
        """)
        f_lay = QVBoxLayout(form_frame)
        f_lay.setContentsMargins(18, 18, 18, 18)
        f_lay.setSpacing(14)

        form_header = QLabel("EXTRACTED RECEIPT DETAILS")
        form_header.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 700; letter-spacing: 0.5px;")
        f_lay.addWidget(form_header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(14)

        def make_field_cell(label_text: str, widget: QWidget) -> QWidget:
            cell = QWidget()
            c_lay = QVBoxLayout(cell)
            c_lay.setContentsMargins(0, 0, 0, 0)
            c_lay.setSpacing(6)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
            widget.setFixedHeight(38)
            c_lay.addWidget(lbl)
            c_lay.addWidget(widget)
            return cell

        # Merchant Input (Full Width)
        self.merchant_input = QLineEdit()
        self.merchant_input.setPlaceholderText("e.g. DMart, Shell Station, Apollo")
        grid.addWidget(make_field_cell("MERCHANT / STORE NAME *", self.merchant_input), 0, 0, 1, 2)

        # Row 1: Amount & Date
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("e.g. 2500.00")
        grid.addWidget(make_field_cell("AMOUNT (₹) *", self.amount_input), 1, 0)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        grid.addWidget(make_field_cell("BILL DATE *", self.date_edit), 1, 1)

        # Row 2: Category & Account
        self.cat_combo = QComboBox()
        categories = CategoryService.get_categories_by_type("Expense")
        for c in categories:
            self.cat_combo.addItem(c.name, c.id)
        grid.addWidget(make_field_cell("EXPENSE CATEGORY *", self.cat_combo), 2, 0)

        self.account_combo = QComboBox()
        accounts = AccountService.get_all_accounts()
        for a in accounts:
            self.account_combo.addItem(f"{a.name}", a.id)
        grid.addWidget(make_field_cell("PAYMENT ACCOUNT *", self.account_combo), 2, 1)

        # Row 3: Paid By & Beneficiary
        self.payer_combo = QComboBox()
        members = FamilyService.get_all_members()
        for m in members:
            self.payer_combo.addItem(f"👤 {m.name}", m.id)
        grid.addWidget(make_field_cell("PAID BY MEMBER *", self.payer_combo), 3, 0)

        self.beneficiary_combo = QComboBox()
        for m in members:
            self.beneficiary_combo.addItem(f"👤 {m.name}", m.id)
        grid.addWidget(make_field_cell("EXPENSE FOR MEMBER *", self.beneficiary_combo), 3, 1)

        # Row 4: Payment Method & Status Card
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["UPI / QR", "Credit Card", "Debit Card", "Cash", "Net Banking"])
        grid.addWidget(make_field_cell("PAYMENT METHOD", self.mode_combo), 4, 0)

        status_container = QFrame()
        status_container.setFixedHeight(38)
        status_container.setStyleSheet("background-color: #0f172a; border: 1px solid #334155; border-radius: 6px;")
        s_box = QHBoxLayout(status_container)
        s_box.setContentsMargins(12, 0, 12, 0)
        self.status_lbl = QLabel("Ready to scan")
        self.status_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        s_box.addWidget(self.status_lbl)
        grid.addWidget(make_field_cell("SCANNER STATUS", status_container), 4, 1)

        f_lay.addLayout(grid)
        f_lay.addStretch(1)

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)
        btn_box.setContentsMargins(0, 10, 0, 0)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155; color: #f8fafc; font-weight: 600;
                padding: 0 20px; border-radius: 6px; border: none; font-size: 13px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("✓ Confirm & Record Expense")
        save_btn.setFixedHeight(40)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d2aa; color: #0b1120; font-weight: 700;
                padding: 0 24px; border-radius: 6px; border: none; font-size: 13px;
            }
            QPushButton:hover { background-color: #20e3b2; }
        """)
        save_btn.clicked.connect(self.save_and_attach)

        btn_box.addStretch()
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)
        f_lay.addLayout(btn_box)

        scroll_area.setWidget(form_frame)
        splitter.addWidget(scroll_area)

        splitter.setSizes([380, 540])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
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
            self.image_preview_lbl.setStyleSheet("background: transparent; padding: 10px;")
            self.image_preview_lbl.setPixmap(pix.scaled(340, 440, Qt.KeepAspectRatio, Qt.SmoothTransformation))
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
        self.status_lbl.setText(f"OCR Match: {conf}% confidence")
        self.status_lbl.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 600;")

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
