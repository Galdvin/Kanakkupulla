"""
Double-Entry General Ledger Explorer View:
Allows accountants, family heads, and users to inspect balanced journals,
audit trail, reconciliation status, and verify that Total Debits == Total Credits.
"""
from datetime import date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
    QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from core.accounting_service_engine import AccountingEngineService
from core.accounting_service import AccountService
from core.financial_utils import format_inr, format_date

class GeneralLedgerView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_ledger()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Double-Entry General Ledger")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #14b8a6;")
        sub = QLabel("Inspect balanced journal entries, account reconciliations, and audit logs")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        verify_btn = QPushButton("⚖ Verify Ledger Balance")
        verify_btn.clicked.connect(self.run_balance_verification)
        header.addWidget(verify_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_ledger)
        header.addWidget(refresh_btn)
        root.addLayout(header)

        # Filter Bar
        filter_card = QFrame()
        filter_card.setProperty("class", "Card")
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(12, 10, 12, 10)

        filter_layout.addWidget(QLabel("Account Filter:"))
        self.acc_combo = QComboBox()
        self.acc_combo.addItem("All Accounts (Full General Ledger)", None)
        for acc in AccountService.get_all_accounts():
            self.acc_combo.addItem(f"{acc.name} ({acc.account_type})", acc.id)
        self.acc_combo.currentIndexChanged.connect(self.load_ledger)
        filter_layout.addWidget(self.acc_combo)

        filter_layout.addStretch()

        self.debits_lbl = QLabel("Debits: ₹0.00")
        self.debits_lbl.setStyleSheet("font-weight: 700; color: #10b981; font-size: 14px;")
        filter_layout.addWidget(self.debits_lbl)

        self.credits_lbl = QLabel("Credits: ₹0.00")
        self.credits_lbl.setStyleSheet("font-weight: 700; color: #ef4444; font-size: 14px; padding-left: 15px;")
        filter_layout.addWidget(self.credits_lbl)

        self.balance_status_lbl = QLabel("BALANCED ✓")
        self.balance_status_lbl.setStyleSheet("font-weight: 800; color: #14b8a6; padding-left: 20px;")
        filter_layout.addWidget(self.balance_status_lbl)

        root.addWidget(filter_card)

        # Journal Table
        self.table = QTableWidget()
        headers = ["Entry ID", "Txn ID", "Date", "Account", "Description", "Debit (₹)", "Credit (₹)"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table)

    def load_ledger(self):
        acc_id = self.acc_combo.currentData()
        entries, count, summary = AccountingEngineService.get_general_ledger_entries(account_id=acc_id)

        self.table.setRowCount(len(entries))
        for row, e in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(str(e.id)))
            self.table.setItem(row, 1, QTableWidgetItem(str(e.transaction_id)))
            self.table.setItem(row, 2, QTableWidgetItem(format_date(e.entry_date)))
            self.table.setItem(row, 3, QTableWidgetItem(e.account.name if e.account else "-"))
            self.table.setItem(row, 4, QTableWidgetItem(e.description or "-"))

            # Debit column
            if e.entry_type == "DEBIT":
                d_item = QTableWidgetItem(format_inr(e.amount_paise))
                d_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                d_item.setForeground(Qt.green)
                self.table.setItem(row, 5, d_item)
                self.table.setItem(row, 6, QTableWidgetItem("-"))
            else: # CREDIT
                self.table.setItem(row, 5, QTableWidgetItem("-"))
                c_item = QTableWidgetItem(format_inr(e.amount_paise))
                c_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                c_item.setForeground(Qt.red)
                self.table.setItem(row, 6, c_item)

        self.debits_lbl.setText(f"Debits: {format_inr(summary['total_debits'])}")
        self.credits_lbl.setText(f"Credits: {format_inr(summary['total_credits'])}")
        if summary["is_balanced"]:
            self.balance_status_lbl.setText("BALANCED ✓")
            self.balance_status_lbl.setStyleSheet("font-weight: 800; color: #14b8a6; padding-left: 20px;")
        else:
            self.balance_status_lbl.setText("UNBALANCED ✗")
            self.balance_status_lbl.setStyleSheet("font-weight: 800; color: #ef4444; padding-left: 20px;")

    def run_balance_verification(self):
        result = AccountingEngineService.verify_ledger_integrity()
        if result["is_system_balanced"] and result["unbalanced_transaction_count"] == 0:
            QMessageBox.information(
                self, "Ledger Integrity Verified",
                f"Double-Entry Accounting Check Passed!\n\n"
                f"Total Entries Audited: {result['total_entries']}\n"
                f"Total Debits: {format_inr(result['total_debits_paise'])}\n"
                f"Total Credits: {format_inr(result['total_credits_paise'])}\n"
                f"Equation Invariant: Total Debits == Total Credits (Balanced)"
            )
        else:
            QMessageBox.critical(
                self, "Ledger Integrity Warning",
                f"Found {result['unbalanced_transaction_count']} unbalanced journal transactions!\n"
                f"Unbalanced IDs: {result['unbalanced_transaction_ids']}"
            )
