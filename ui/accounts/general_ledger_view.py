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
from PySide6.QtGui import QColor
from core.accounting_service_engine import AccountingEngineService
from core.accounting_service import AccountService
from core.financial_utils import format_inr, format_date
from ui.table_helper import configure_fintech_table, LEDGER_WIDTHS

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

        filter_layout.addWidget(QLabel("View Mode:"))
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItem("🏦 Bank Passbook Statement (Debits = Expenses, Credits = Income)", "PASSBOOK")
        self.view_mode_combo.addItem("⚖ Double-Entry Journal (Accounting Books)", "JOURNAL")
        self.view_mode_combo.currentIndexChanged.connect(self.load_ledger)
        filter_layout.addWidget(self.view_mode_combo)

        filter_layout.addWidget(QLabel("Account:"))
        self.acc_combo = QComboBox()
        self.acc_combo.addItem("All Accounts", None)
        for acc in AccountService.get_all_accounts():
            self.acc_combo.addItem(f"{acc.name} ({acc.account_type})", acc.id)
        self.acc_combo.currentIndexChanged.connect(self.load_ledger)
        filter_layout.addWidget(self.acc_combo)

        filter_layout.addStretch()

        self.metric1_lbl = QLabel("Expenses: ₹0.00")
        self.metric1_lbl.setStyleSheet("font-weight: 700; color: #fb7185; font-size: 14px;")
        filter_layout.addWidget(self.metric1_lbl)

        self.metric2_lbl = QLabel("Income: ₹0.00")
        self.metric2_lbl.setStyleSheet("font-weight: 700; color: #10b981; font-size: 14px; padding-left: 15px;")
        filter_layout.addWidget(self.metric2_lbl)

        self.metric3_lbl = QLabel("Net: ₹0.00")
        self.metric3_lbl.setStyleSheet("font-weight: 800; color: #38bdf8; padding-left: 20px;")
        filter_layout.addWidget(self.metric3_lbl)

        root.addWidget(filter_card)

        # Informational Guidance Banner
        self.info_card = QFrame()
        self.info_card.setStyleSheet("background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px; padding: 6px 12px;")
        info_layout = QHBoxLayout(self.info_card)
        info_layout.setContentsMargins(10, 6, 10, 6)
        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        info_layout.addWidget(self.info_lbl)
        root.addWidget(self.info_card)

        # Journal / Statement Table
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table)

    def load_ledger(self):
        acc_id = self.acc_combo.currentData()
        mode = self.view_mode_combo.currentData()

        if mode == "PASSBOOK":
            # 1. Retail Bank Passbook Format (Expenses = Debits, Income = Credits)
            headers = ["Txn ID", "Date", "Account", "Description", "Category / Head", "Debit / Money Out (₹)", "Credit / Money In (₹)"]
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            configure_fintech_table(self.table, stretch_col=3, col_widths={
                0: 70, 1: 100, 2: 170, 3: 200, 4: 150, 5: 140, 6: 140
            })

            txns, count, summary = AccountingEngineService.get_bank_passbook_entries(account_id=acc_id)
            self.table.setRowCount(len(txns))

            for row, t in enumerate(txns):
                self.table.setItem(row, 0, QTableWidgetItem(str(t.id)))
                self.table.setItem(row, 1, QTableWidgetItem(format_date(t.transaction_date)))
                self.table.setItem(row, 2, QTableWidgetItem(t.account.name if t.account else "-"))
                self.table.setItem(row, 3, QTableWidgetItem(t.title or "-"))
                cat_name = t.category.name if t.category else (t.expense_kind or ("Income" if t.transaction_type == "Income" else "General"))
                self.table.setItem(row, 4, QTableWidgetItem(cat_name))

                if t.transaction_type == "Income":
                    self.table.setItem(row, 5, QTableWidgetItem("-"))
                    c_item = QTableWidgetItem(format_inr(t.amount_paise))
                    c_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    c_item.setForeground(QColor("#10b981"))
                    self.table.setItem(row, 6, c_item)
                else: # Expense / Payment
                    d_item = QTableWidgetItem(format_inr(t.amount_paise))
                    d_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    d_item.setForeground(QColor("#fb7185"))
                    self.table.setItem(row, 5, d_item)
                    self.table.setItem(row, 6, QTableWidgetItem("-"))

            self.metric1_lbl.setText(f"Expenses (Debited): {format_inr(summary['total_debits'])}")
            self.metric1_lbl.setStyleSheet("font-weight: 700; color: #fb7185; font-size: 14px;")
            self.metric2_lbl.setText(f"Income (Credited): {format_inr(summary['total_credits'])}")
            self.metric2_lbl.setStyleSheet("font-weight: 700; color: #10b981; font-size: 14px; padding-left: 15px;")
            net = summary["net_inflow"]
            net_prefix = "+" if net >= 0 else ""
            self.metric3_lbl.setText(f"Net Savings: {net_prefix}{format_inr(net)}")
            self.metric3_lbl.setStyleSheet(f"font-weight: 800; color: {'#38bdf8' if net >= 0 else '#ef4444'}; padding-left: 20px;")
            self.info_lbl.setText("💡 Bank Passbook View: Money spent (Petrol ₹220, Groceries ₹320) is recorded as Debits (Money Out). Only income receipts (Salary ₹50,000) are recorded as Credits (Money In).")

        else:
            # 2. Formal Double-Entry Journal Mode
            headers = ["Entry ID", "Txn ID", "Date", "Ledger Account", "Description", "Debit (₹)", "Credit (₹)"]
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            configure_fintech_table(self.table, stretch_col=4, col_widths=LEDGER_WIDTHS)

            entries, count, summary = AccountingEngineService.get_general_ledger_entries(account_id=acc_id)
            self.table.setRowCount(len(entries))

            for row, e in enumerate(entries):
                self.table.setItem(row, 0, QTableWidgetItem(str(e.id)))
                self.table.setItem(row, 1, QTableWidgetItem(str(e.transaction_id)))
                self.table.setItem(row, 2, QTableWidgetItem(format_date(e.entry_date)))

                # Meaningful double-entry account distinction
                desc = e.description or ""
                if e.entry_type == "CREDIT" and desc.startswith("Paid for:"):
                    acc_display = f"{e.account.name} (Asset Outflow)" if e.account else "Cash/Bank Account"
                elif e.entry_type == "DEBIT" and desc.startswith("Expense Category:"):
                    cat_name = e.transaction.category.name if (e.transaction and e.transaction.category) else (e.transaction.title if e.transaction else "Expense")
                    acc_display = f"Expense: {cat_name} (Expense Incurred)"
                elif e.entry_type == "DEBIT" and desc.startswith("Received Income:"):
                    acc_display = f"{e.account.name} (Asset Inflow)" if e.account else "Bank Account"
                elif e.entry_type == "CREDIT" and desc.startswith("Revenue Credit:"):
                    acc_display = f"Revenue: {e.transaction.title if e.transaction else 'Income'} (Revenue Earned)"
                else:
                    acc_display = e.account.name if e.account else "-"

                self.table.setItem(row, 3, QTableWidgetItem(acc_display))
                self.table.setItem(row, 4, QTableWidgetItem(desc or "-"))

                # Debit column
                if e.entry_type == "DEBIT":
                    d_item = QTableWidgetItem(format_inr(e.amount_paise))
                    d_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    d_item.setForeground(QColor("#10b981"))
                    self.table.setItem(row, 5, d_item)
                    self.table.setItem(row, 6, QTableWidgetItem("-"))
                else: # CREDIT
                    self.table.setItem(row, 5, QTableWidgetItem("-"))
                    c_item = QTableWidgetItem(format_inr(e.amount_paise))
                    c_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    c_item.setForeground(QColor("#fb7185"))
                    self.table.setItem(row, 6, c_item)

            self.metric1_lbl.setText(f"Total Debits: {format_inr(summary['total_debits'])}")
            self.metric1_lbl.setStyleSheet("font-weight: 700; color: #10b981; font-size: 14px;")
            self.metric2_lbl.setText(f"Total Credits: {format_inr(summary['total_credits'])}")
            self.metric2_lbl.setStyleSheet("font-weight: 700; color: #ef4444; font-size: 14px; padding-left: 15px;")
            if summary["is_balanced"]:
                self.metric3_lbl.setText("BALANCED ✓")
                self.metric3_lbl.setStyleSheet("font-weight: 800; color: #14b8a6; padding-left: 20px;")
            else:
                self.metric3_lbl.setText("UNBALANCED ✗")
                self.metric3_lbl.setStyleSheet("font-weight: 800; color: #ef4444; padding-left: 20px;")
            self.info_lbl.setText("💡 Double-Entry Bookkeeping Rule: In formal accounting books, cash asset accounts credit when money goes out (Credit ₹220) and debit when money enters (Debit ₹50,000) to balance with category nominal accounts.")

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
