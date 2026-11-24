"""
Investment Dialogs:
- InvestmentDialog: Add mutual funds, stocks, gold, PPF, FDs.
- UpdateValuationDialog: Quickly record latest NAV / market price.
"""
from typing import Optional
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QDateEdit, QPushButton, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt, QDate
from core.family_service import FamilyService
from core.investment_service import InvestmentService

ASSET_TYPES = [
    "Mutual Funds",
    "Stocks / Equity",
    "Gold & Precious Metals",
    "Fixed Deposit (FD)",
    "Recurring Deposit (RD)",
    "PPF / EPF / VPF",
    "NPS (Pension)",
    "Real Estate",
    "Bonds / Debentures",
    "Crypto Assets",
    "Other Assets"
]

class InvestmentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Investment Holding")
        self.setFixedSize(520, 620)
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; color: #f8fafc; }
            QLabel { color: #94a3b8; font-size: 13px; font-weight: 500; }
            QLineEdit, QComboBox, QDateEdit, QTextEdit {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 6px; padding: 8px 12px; color: #f8fafc; font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
                border: 1px solid #0ea5e9;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("New Asset / Investment")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(title)

        # Asset Name
        layout.addWidget(QLabel("Asset / Holding Name *"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Parag Parikh Flexi Cap, Sovereign Gold Bond 2024")
        layout.addWidget(self.name_input)

        # Member & Asset Type Row
        row1 = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Family Member *"))
        self.member_combo = QComboBox()
        members = FamilyService.get_all_members()
        for m in members:
            self.member_combo.addItem(f"👤 {m.name} ({m.relation_type})", m.id)
        v1.addWidget(self.member_combo)
        row1.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Asset Class *"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(ASSET_TYPES)
        v2.addWidget(self.type_combo)
        row1.addLayout(v2)
        layout.addLayout(row1)

        # Invested Amount & Current Value Row
        row2 = QHBoxLayout()
        v3 = QVBoxLayout()
        v3.addWidget(QLabel("Invested Amount (₹) *"))
        self.invested_input = QLineEdit()
        self.invested_input.setPlaceholderText("e.g. 50000")
        v3.addWidget(self.invested_input)
        row2.addLayout(v3)

        v4 = QVBoxLayout()
        v4.addWidget(QLabel("Current Valuation (₹) *"))
        self.current_input = QLineEdit()
        self.current_input.setPlaceholderText("e.g. 55000")
        v4.addWidget(self.current_input)
        row2.addLayout(v4)
        layout.addLayout(row2)

        # Investment Date & Maturity Date
        row3 = QHBoxLayout()
        v5 = QVBoxLayout()
        v5.addWidget(QLabel("Investment Date *"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        t = date.today()
        self.date_edit.setDate(QDate(t.year, t.month, t.day))
        v5.addWidget(self.date_edit)
        row3.addLayout(v5)

        v6 = QVBoxLayout()
        v6.addWidget(QLabel("Maturity Date (Optional)"))
        self.mat_date_edit = QDateEdit()
        self.mat_date_edit.setCalendarPopup(True)
        self.mat_date_edit.setDate(QDate(t.year + 3, t.month, t.day))
        v6.addWidget(self.mat_date_edit)
        row3.addLayout(v6)
        layout.addLayout(row3)

        # Institution & Folio
        row4 = QHBoxLayout()
        v7 = QVBoxLayout()
        v7.addWidget(QLabel("Institution / Broker / AMC"))
        self.inst_input = QLineEdit()
        self.inst_input.setPlaceholderText("e.g. Zerodha, Groww, SBI Bank")
        v7.addWidget(self.inst_input)
        row4.addLayout(v7)

        v8 = QVBoxLayout()
        v8.addWidget(QLabel("Folio / Account / Demat ID"))
        self.folio_input = QLineEdit()
        self.folio_input.setPlaceholderText("e.g. 12345678/90")
        v8.addWidget(self.folio_input)
        row4.addLayout(v8)
        layout.addLayout(row4)

        # Notes
        layout.addWidget(QLabel("Notes (Optional)"))
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("SIP details, lock-in period, etc.")
        layout.addWidget(self.notes_input)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #334155; color: #f8fafc; padding: 9px 18px; border-radius: 6px;")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Add Investment")
        save_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: 600; padding: 9px 18px; border-radius: 6px;")
        save_btn.clicked.connect(self.save)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Investment name is required.")
            return

        member_id = self.member_combo.currentData()
        if not member_id:
            QMessageBox.warning(self, "Validation Error", "Please select a family member.")
            return

        try:
            invested_rs = float(self.invested_input.text().strip() or "0")
            if invested_rs <= 0:
                raise ValueError()
            invested_paise = int(round(invested_rs * 100))
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid invested amount.")
            return

        try:
            curr_rs = float(self.current_input.text().strip() or str(invested_rs))
            if curr_rs < 0:
                raise ValueError()
            curr_paise = int(round(curr_rs * 100))
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid current valuation.")
            return

        d = self.date_edit.date()
        inv_date = date(d.year(), d.month(), d.day())
        asset_type = self.type_combo.currentText()
        inst = self.inst_input.text().strip() or None
        folio = self.folio_input.text().strip() or None
        notes = self.notes_input.text().strip() or None

        success, msg, _ = InvestmentService.add_investment(
            family_member_id=member_id,
            investment_name=name,
            investment_type=asset_type,
            invested_amount_paise=invested_paise,
            current_value_paise=curr_paise,
            investment_date=inv_date,
            institution=inst,
            folio_or_id=folio,
            notes=notes
        )

        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to add investment: {msg}")


class UpdateValuationDialog(QDialog):
    def __init__(self, preselected_inv_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Asset Market Valuation")
        self.setFixedSize(440, 320)
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; color: #f8fafc; }
            QLabel { color: #94a3b8; font-size: 13px; font-weight: 500; }
            QLineEdit, QComboBox {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 6px; padding: 8px 12px; color: #f8fafc; font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #0ea5e9; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Update Market Value")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Select Investment Holding *"))
        self.inv_combo = QComboBox()
        investments = InvestmentService.get_all_investments()
        for inv in investments:
            self.inv_combo.addItem(f"{inv.investment_name} (Current: ₹{inv.current_value_paise/100:,.2f})", inv.id)
            if preselected_inv_id and inv.id == preselected_inv_id:
                self.inv_combo.setCurrentIndex(self.inv_combo.count() - 1)
        layout.addWidget(self.inv_combo)

        layout.addWidget(QLabel("New Market Valuation (₹) *"))
        self.new_val_input = QLineEdit()
        self.new_val_input.setPlaceholderText("e.g. 62500")
        layout.addWidget(self.new_val_input)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #334155; color: #f8fafc; padding: 9px 18px; border-radius: 6px;")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Update Value")
        save_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: 600; padding: 9px 18px; border-radius: 6px;")
        save_btn.clicked.connect(self.save)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def save(self):
        inv_id = self.inv_combo.currentData()
        if not inv_id:
            QMessageBox.warning(self, "Validation Error", "No investment selected.")
            return

        try:
            new_rs = float(self.new_val_input.text().strip() or "0")
            if new_rs < 0:
                raise ValueError()
            new_paise = int(round(new_rs * 100))
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid positive valuation.")
            return

        success, msg = InvestmentService.update_valuation(inv_id, new_paise)
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to update valuation: {msg}")
