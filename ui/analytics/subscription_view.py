"""
Subscription Management View:
Tracks recurring commitments (OTT, broadband, mobile, insurance, memberships).
Highlights upcoming renewals and monthly/annual burn rate.
"""
from datetime import date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, 
    QLineEdit, QComboBox, QMessageBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from core.subscription_service import SubscriptionService
from core.accounting_service import AccountService
from core.user_service import UserService
from core.financial_utils import format_inr, inr_to_paise, format_date
from config.constants import RecurringFrequency
from ui.table_helper import configure_fintech_table, SUBSCRIPTION_WIDTHS

class AddSubscriptionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Subscription / Recurring Payment")
        self.setFixedSize(420, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        layout.addWidget(QLabel("Subscription Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Netflix Premium, JioFiber, Health Insurance")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Billing Frequency:"))
        self.freq_combo = QComboBox()
        self.freq_combo.addItems([
            RecurringFrequency.MONTHLY.value,
            RecurringFrequency.YEARLY.value,
            RecurringFrequency.QUARTERLY.value
        ])
        layout.addWidget(self.freq_combo)

        layout.addWidget(QLabel("Billing Amount (₹):"))
        self.amt_input = QLineEdit()
        self.amt_input.setPlaceholderText("0.00")
        layout.addWidget(self.amt_input)

        layout.addWidget(QLabel("Next Renewal Date:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate().addMonths(1))
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        layout.addWidget(self.date_edit)

        layout.addWidget(QLabel("Payment Account:"))
        self.acc_combo = QComboBox()
        for acc in AccountService.get_all_accounts():
            self.acc_combo.addItem(acc.name, acc.id)
        layout.addWidget(self.acc_combo)

        layout.addSpacing(10)
        save_btn = QPushButton("Save Subscription")
        save_btn.setProperty("class", "PrimaryBtn")
        save_btn.clicked.connect(self.save)
        layout.addWidget(save_btn)

    def save(self):
        title = self.name_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation", "Subscription name is required")
            return

        try:
            amt_paise = inr_to_paise(float(self.amt_input.text().strip()))
            if amt_paise <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Validation", "Invalid billing amount")
            return

        freq = self.freq_combo.currentText()
        acc_id = self.acc_combo.currentData()
        qdate = self.date_edit.date()
        next_due = date(qdate.year(), qdate.month(), qdate.day())
        user_id = UserService.get_all_users()[0].id

        ok, msg = SubscriptionService.add_subscription(
            title=title,
            amount_paise=amt_paise,
            frequency=freq,
            start_date=date.today(),
            next_due_date=next_due,
            account_id=acc_id,
            paid_by_id=user_id
        )
        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", msg)


class SubscriptionView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Subscription & Recurring Payments")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #38bdf8;")
        sub = QLabel("Track OTT, broadband, memberships, and optimize unwanted recurring charges")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.add_btn = QPushButton("+ Add Subscription")
        self.add_btn.setProperty("class", "PrimaryBtn")
        self.add_btn.clicked.connect(self.open_add_dialog)
        header.addWidget(self.add_btn)
        root.addLayout(header)

        # Table
        self.table = QTableWidget()
        headers = ["Subscription", "Frequency", "Billed Amount", "Monthly Cost", "Annual Cost", "Next Renewal", "Status"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        configure_fintech_table(self.table, stretch_col=0, col_widths=SUBSCRIPTION_WIDTHS)
        root.addWidget(self.table)

        # Footer Metrics
        footer = QHBoxLayout()
        self.monthly_burn_lbl = QLabel("Monthly Burn: ₹0.00")
        self.monthly_burn_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #f59e0b;")
        footer.addWidget(self.monthly_burn_lbl)

        self.annual_burn_lbl = QLabel("Annual Burn: ₹0.00")
        self.annual_burn_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #ef4444; padding-left: 20px;")
        footer.addWidget(self.annual_burn_lbl)

        footer.addStretch()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        footer.addWidget(refresh_btn)
        root.addLayout(footer)

    def load_data(self):
        subs = SubscriptionService.get_all_subscriptions()
        self.table.setRowCount(len(subs))

        total_monthly = sum(s["monthly_paise"] for s in subs)
        total_annual = sum(s["annual_paise"] for s in subs)

        for row, s in enumerate(subs):
            self.table.setItem(row, 0, QTableWidgetItem(s["title"]))
            self.table.setItem(row, 1, QTableWidgetItem(s["frequency"]))
            self.table.setItem(row, 2, QTableWidgetItem(format_inr(s["amount_paise"])))
            self.table.setItem(row, 3, QTableWidgetItem(format_inr(s["monthly_paise"])))
            self.table.setItem(row, 4, QTableWidgetItem(format_inr(s["annual_paise"])))
            self.table.setItem(row, 5, QTableWidgetItem(format_date(s["next_due_date"])))
            self.table.setItem(row, 6, QTableWidgetItem("Active" if s["is_active"] else "Paused"))

        self.monthly_burn_lbl.setText(f"Monthly Burn: {format_inr(total_monthly)}")
        self.annual_burn_lbl.setText(f"Annual Burn: {format_inr(total_annual)}")

    def open_add_dialog(self):
        dlg = AddSubscriptionDialog(parent=self)
        if dlg.exec():
            self.load_data()
