"""
Bank Accounts, Cash, and Cards View with Transfer Dialog
"""
from datetime import date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, 
    QLineEdit, QComboBox, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QDate
from core.accounting_service import AccountService
from core.financial_utils import format_inr, inr_to_paise
from config.constants import AccountType
from ui.table_helper import configure_fintech_table, ACCOUNTS_WIDTHS

class AccountCreateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Bank Account / Card / Wallet")
        self.setFixedSize(400, 380)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        layout.addWidget(QLabel("Account Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. HDFC Salary Acc, Amazon Pay Wallet")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Account Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            AccountType.SAVINGS.value,
            AccountType.CURRENT.value,
            AccountType.CASH.value,
            AccountType.UPI.value,
            AccountType.DIGITAL_WALLET.value,
            AccountType.CREDIT_CARD.value,
            AccountType.FIXED_DEPOSIT.value
        ])
        layout.addWidget(self.type_combo)

        layout.addWidget(QLabel("Opening Balance (₹):"))
        self.bal_input = QLineEdit()
        self.bal_input.setPlaceholderText("0.00")
        self.bal_input.setText("0.00")
        layout.addWidget(self.bal_input)

        layout.addWidget(QLabel("Bank / Institution Name (Optional):"))
        self.bank_input = QLineEdit()
        self.bank_input.setPlaceholderText("e.g. State Bank of India")
        layout.addWidget(self.bank_input)

        layout.addSpacing(10)
        save_btn = QPushButton("Save Account")
        save_btn.setProperty("class", "PrimaryBtn")
        save_btn.clicked.connect(self.save)
        layout.addWidget(save_btn)

    def save(self):
        name = self.name_input.text().strip()
        acc_type = self.type_combo.currentText()
        if not name:
            QMessageBox.warning(self, "Validation", "Account name is required")
            return

        try:
            bal_paise = inr_to_paise(float(self.bal_input.text().strip()))
        except ValueError:
            QMessageBox.warning(self, "Validation", "Invalid opening balance")
            return

        ok, msg, _ = AccountService.create_account(
            name=name,
            account_type=acc_type,
            opening_balance_paise=bal_paise,
            institution_name=self.bank_input.text().strip() or None
        )
        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", msg)


class TransferDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Internal Fund Transfer")
        self.setFixedSize(400, 360)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        layout.addWidget(QLabel("Transfer From:"))
        self.from_combo = QComboBox()
        layout.addWidget(self.from_combo)

        layout.addWidget(QLabel("Transfer To:"))
        self.to_combo = QComboBox()
        layout.addWidget(self.to_combo)

        layout.addWidget(QLabel("Transfer Amount (₹):"))
        self.amt_input = QLineEdit()
        self.amt_input.setPlaceholderText("0.00")
        layout.addWidget(self.amt_input)

        layout.addWidget(QLabel("Note / Remarks:"))
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("e.g. ATM cash withdrawal, CC bill payment")
        layout.addWidget(self.note_input)

        # Populate accounts
        accounts = AccountService.get_all_accounts()
        for acc in accounts:
            label = f"{acc.name} ({format_inr(acc.current_balance_paise)})"
            self.from_combo.addItem(label, acc.id)
            self.to_combo.addItem(label, acc.id)

        if len(accounts) > 1:
            self.to_combo.setCurrentIndex(1)

        layout.addSpacing(10)
        transfer_btn = QPushButton("Execute Transfer")
        transfer_btn.setProperty("class", "PrimaryBtn")
        transfer_btn.clicked.connect(self.execute)
        layout.addWidget(transfer_btn)

    def execute(self):
        from_id = self.from_combo.currentData()
        to_id = self.to_combo.currentData()
        if from_id == to_id:
            QMessageBox.warning(self, "Validation", "Source and destination accounts must be different")
            return

        try:
            amt_paise = inr_to_paise(float(self.amt_input.text().strip()))
            if amt_paise <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Validation", "Please enter a valid positive transfer amount")
            return

        ok, msg = AccountService.transfer_funds(
            from_account_id=from_id,
            to_account_id=to_id,
            amount_paise=amt_paise,
            transfer_date=date.today(),
            reference_note=self.note_input.text().strip() or None
        )
        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", msg)


class AccountsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_accounts()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Accounts, Cards & Balances")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #38bdf8;")
        sub = QLabel("Manage bank accounts, wallets, cash balances, and internal fund transfers")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.transfer_btn = QPushButton("⇄ Transfer Funds")
        self.transfer_btn.clicked.connect(self.open_transfer_dialog)
        header.addWidget(self.transfer_btn)

        self.add_acc_btn = QPushButton("+ Add Account")
        self.add_acc_btn.setProperty("class", "PrimaryBtn")
        self.add_acc_btn.clicked.connect(self.open_create_dialog)
        header.addWidget(self.add_acc_btn)

        layout.addLayout(header)

        # Table
        self.table = QTableWidget()
        headers = ["ID", "Account Name", "Account Type", "Institution", "Opening Balance", "Current Balance"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        configure_fintech_table(self.table, stretch_col=1, col_widths=ACCOUNTS_WIDTHS)
        layout.addWidget(self.table)

        # Total net liquid balance
        footer = QHBoxLayout()
        self.total_bal_lbl = QLabel("Total Net Liquid Balance: ₹0.00")
        self.total_bal_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        footer.addWidget(self.total_bal_lbl)
        footer.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_accounts)
        footer.addWidget(refresh_btn)
        layout.addLayout(footer)

    def load_accounts(self):
        accounts = AccountService.get_all_accounts()
        self.table.setRowCount(len(accounts))
        total_paise = 0

        for row, acc in enumerate(accounts):
            total_paise += acc.current_balance_paise
            self.table.setItem(row, 0, QTableWidgetItem(str(acc.id)))
            self.table.setItem(row, 1, QTableWidgetItem(acc.name))
            self.table.setItem(row, 2, QTableWidgetItem(acc.account_type))
            self.table.setItem(row, 3, QTableWidgetItem(acc.institution_name or "-"))

            op_item = QTableWidgetItem(format_inr(acc.opening_balance_paise))
            op_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, op_item)

            bal_item = QTableWidgetItem(format_inr(acc.current_balance_paise))
            bal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 5, bal_item)

        self.total_bal_lbl.setText(f"Total Net Balance: {format_inr(total_paise)}")

    def open_create_dialog(self):
        dlg = AccountCreateDialog(parent=self)
        if dlg.exec():
            self.load_accounts()

    def open_transfer_dialog(self):
        dlg = TransferDialog(parent=self)
        if dlg.exec():
            self.load_accounts()
