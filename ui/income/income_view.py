"""
Income Management View & Entry Dialog
"""
from datetime import date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
    QLineEdit, QDateEdit, QMessageBox, QFrame, QDialog
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from core.income_service import IncomeService
from core.family_service import FamilyService
from core.accounting_service import AccountService
from core.financial_utils import format_inr, inr_to_paise, format_date
from config.constants import DEFAULT_INCOME_SOURCES
from ui.table_helper import configure_fintech_table, INCOME_WIDTHS

class IncomeEntryDialog(QDialog):
    def __init__(self, income=None, parent=None):
        super().__init__(parent)
        self.income = income
        self.is_edit = income is not None
        self.setWindowTitle("Edit Income" if self.is_edit else "Record Income")
        self.resize(500, 560)
        self.setMinimumSize(460, 500)
        self.init_ui()
        if self.is_edit:
            self.populate_existing_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(28, 24, 28, 24)

        # Source / Title
        layout.addWidget(QLabel("Income Source / Title:"))
        self.source_combo = QComboBox()
        self.source_combo.setEditable(True)
        self.source_combo.addItems(DEFAULT_INCOME_SOURCES)
        self.source_combo.setFixedHeight(38)
        layout.addWidget(self.source_combo)

        # Amount & Date row
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        vbox_amt = QVBoxLayout()
        vbox_amt.addWidget(QLabel("Amount Received (₹):"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        self.amount_input.setFixedHeight(38)
        vbox_amt.addWidget(self.amount_input)
        row1.addLayout(vbox_amt)

        vbox_date = QVBoxLayout()
        vbox_date.addWidget(QLabel("Date Credited:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        self.date_edit.setFixedHeight(38)
        vbox_date.addWidget(self.date_edit)
        row1.addLayout(vbox_date)
        layout.addLayout(row1)

        # Destination Account & Mode
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        vbox_acc = QVBoxLayout()
        vbox_acc.addWidget(QLabel("Credited To Account:"))
        self.account_combo = QComboBox()
        self.account_combo.setFixedHeight(38)
        accounts = AccountService.get_all_accounts()
        for acc in accounts:
            self.account_combo.addItem(f"{acc.name} ({acc.account_type})", acc.id)
        vbox_acc.addWidget(self.account_combo)
        row2.addLayout(vbox_acc)

        vbox_mode = QVBoxLayout()
        vbox_mode.addWidget(QLabel("Payment Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.setFixedHeight(38)
        self.mode_combo.addItems(["Bank Transfer", "NEFT / RTGS / IMPS", "UPI", "Cheque", "Cash", "Other"])
        vbox_mode.addWidget(self.mode_combo)
        row2.addLayout(vbox_mode)
        layout.addLayout(row2)

        # Received By (Family Member)
        layout.addWidget(QLabel("Received By (Earner):"))
        self.user_combo = QComboBox()
        self.user_combo.setFixedHeight(38)
        members = FamilyService.get_all_members()
        for m in members:
            role_tag = f" ({m.relation_type})" if m.relation_type else ""
            self.user_combo.addItem(f"👤 {m.name}{role_tag}", m.id)
        layout.addWidget(self.user_combo)

        # Reference No
        layout.addWidget(QLabel("Reference / Cheque / UTR No:"))
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Optional transaction reference")
        self.ref_input.setFixedHeight(38)
        layout.addWidget(self.ref_input)

        layout.addSpacing(10)
        self.save_btn = QPushButton("Save Income")
        self.save_btn.setProperty("class", "PrimaryBtn")
        self.save_btn.setFixedHeight(42)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0d9488, stop:1 #14b8a6);
                color: #ffffff;
                font-weight: 700;
                font-size: 14px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f766e, stop:1 #0d9488);
            }
        """)
        self.save_btn.clicked.connect(self.save)
        layout.addWidget(self.save_btn)

    def populate_existing_data(self):
        if not self.income:
            return
        idx = self.source_combo.findText(self.income.title)
        if idx >= 0:
            self.source_combo.setCurrentIndex(idx)
        else:
            self.source_combo.setEditText(self.income.title or "")

        self.amount_input.setText(f"{self.income.amount_paise / 100:.2f}")
        if self.income.transaction_date:
            d = self.income.transaction_date
            self.date_edit.setDate(QDate(d.year, d.month, d.day))

        if hasattr(self.income, "account_id") and self.income.account_id:
            idx = self.account_combo.findData(self.income.account_id)
            if idx >= 0:
                self.account_combo.setCurrentIndex(idx)

        if hasattr(self.income, "paid_by_member_id") and self.income.paid_by_member_id:
            idx = self.user_combo.findData(self.income.paid_by_member_id)
            if idx >= 0:
                self.user_combo.setCurrentIndex(idx)

        if hasattr(self.income, "payment_method") and self.income.payment_method:
            idx = self.mode_combo.findText(self.income.payment_method)
            if idx >= 0:
                self.mode_combo.setCurrentIndex(idx)

        if hasattr(self.income, "reference_no") and self.income.reference_no:
            self.ref_input.setText(self.income.reference_no)

    def save(self):
        source = self.source_combo.currentText().strip()
        amt_text = self.amount_input.text().strip()
        if not source:
            QMessageBox.warning(self, "Validation", "Source is required")
            return

        try:
            amt_paise = inr_to_paise(float(amt_text))
            if amt_paise <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Validation", "Please enter a valid positive amount")
            return

        qdate = self.date_edit.date()
        inc_date = date(qdate.year(), qdate.month(), qdate.day())
        account_id = self.account_combo.currentData()
        received_by_id = self.user_combo.currentData()
        mode = self.mode_combo.currentText()
        ref = self.ref_input.text().strip() or None

        if not account_id:
            QMessageBox.warning(self, "Validation", "Please select a destination account")
            return

        if not received_by_id:
            QMessageBox.warning(self, "Validation", "Please select an earner (family member)")
            return

        if self.is_edit:
            ok, msg = IncomeService.update_income(
                income_id=self.income.id,
                source_title=source,
                amount_paise=amt_paise,
                income_date=inc_date,
                account_id=account_id,
                received_by_member_id=received_by_id,
                payment_mode=mode,
                reference_no=ref
            )
            if ok:
                self.accept()
            else:
                QMessageBox.critical(self, "Error", msg)
            return

        ok, msg, _ = IncomeService.record_income(
            source_title=source,
            amount_paise=amt_paise,
            income_date=inc_date,
            account_id=account_id,
            received_by_member_id=received_by_id,
            received_by_id=received_by_id,
            payment_mode=mode,
            reference_no=ref
        )

        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", msg)


class IncomeView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_income()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Income Management")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #38bdf8;")
        sub = QLabel("Track salary, investments, freelance, rentals, and all revenue streams")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.add_btn = QPushButton("+ Record Income")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0d9488, stop:1 #14b8a6);
                color: #ffffff;
                font-weight: 700;
                font-size: 13px;
                padding: 8px 18px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f766e, stop:1 #0d9488);
            }
        """)
        self.add_btn.clicked.connect(self.open_add_dialog)
        header.addWidget(self.add_btn)
        layout.addLayout(header)

        # Income Table
        self.table = QTableWidget()
        headers = ["ID", "Date", "Source", "Received By", "Credited Account", "Payment Mode", "Ref No", "Amount"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.open_edit_dialog)
        configure_fintech_table(self.table, stretch_col=2, col_widths=INCOME_WIDTHS)
        layout.addWidget(self.table)

        # Footer
        footer = QHBoxLayout()
        edit_btn = QPushButton("Edit Selected")
        edit_btn.clicked.connect(self.open_edit_dialog)
        footer.addWidget(edit_btn)

        del_btn = QPushButton("Delete Selected")
        del_btn.setProperty("class", "DangerBtn")
        del_btn.clicked.connect(self.delete_selected)
        footer.addWidget(del_btn)

        self.total_lbl = QLabel("Total Income: ₹0.00")
        self.total_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #10b981; padding-left: 15px;")
        footer.addWidget(self.total_lbl)
        footer.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_income)
        footer.addWidget(refresh_btn)
        layout.addLayout(footer)

    def load_income(self):
        incomes, count = IncomeService.get_incomes()
        self.table.setRowCount(len(incomes))
        total_paise = 0

        for row, txn in enumerate(incomes):
            total_paise += txn.amount_paise
            id_item = QTableWidgetItem(str(txn.id))
            id_item.setData(Qt.UserRole, txn.id)
            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, QTableWidgetItem(format_date(txn.transaction_date)))
            self.table.setItem(row, 2, QTableWidgetItem(txn.title))
            member_name = txn.paid_by_member.name if (hasattr(txn, "paid_by_member") and txn.paid_by_member) else "-"
            self.table.setItem(row, 3, QTableWidgetItem(member_name))
            acc_name = txn.account.name if (hasattr(txn, "account") and txn.account) else "-"
            self.table.setItem(row, 4, QTableWidgetItem(acc_name))
            self.table.setItem(row, 5, QTableWidgetItem(txn.payment_method or "-"))
            self.table.setItem(row, 6, QTableWidgetItem(txn.reference_no or "-"))

            amt_item = QTableWidgetItem(format_inr(txn.amount_paise))
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amt_item.setForeground(QColor("#10b981"))
            self.table.setItem(row, 7, amt_item)

        self.total_lbl.setText(f"Total Income: {format_inr(total_paise)}")

    def open_add_dialog(self):
        dlg = IncomeEntryDialog(parent=self)
        if dlg.exec():
            self.load_income()

    def open_edit_dialog(self):
        curr_row = self.table.currentRow()
        if curr_row < 0:
            QMessageBox.information(self, "Selection", "Please select an income record to edit.")
            return

        txn_id = self.table.item(curr_row, 0).data(Qt.UserRole)
        txn = IncomeService.get_income_by_id(txn_id)
        if not txn:
            QMessageBox.warning(self, "Not Found", "Selected income record could not be loaded.")
            return

        dlg = IncomeEntryDialog(income=txn, parent=self)
        if dlg.exec():
            self.load_income()

    def delete_selected(self):
        curr_row = self.table.currentRow()
        if curr_row < 0:
            QMessageBox.information(self, "Selection", "Please select an income record to delete.")
            return

        txn_id = self.table.item(curr_row, 0).data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Confirm Delete", "Are you sure you want to delete this income? Credited account balance will be reverted.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            ok, msg = IncomeService.delete_income(txn_id)
            if ok:
                self.load_income()
            else:
                QMessageBox.critical(self, "Error", msg)
