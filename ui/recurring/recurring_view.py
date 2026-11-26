"""
Recurring Rules & Automation View:
Manages automated schedules for rents, bills, EMIs, and salaries,
with manual and automatic execution triggers.
"""
from typing import Optional
from datetime import date, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from core.recurring_service import RecurringService
from core.family_service import FamilyService
from config.constants import TransactionType
from ui.recurring.recurring_dialog import RecurringRuleDialog
from ui.table_helper import configure_fintech_table

class RecurringView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)

        # Header Bar
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Recurring Transactions & Auto-Rules")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #f8fafc;")
        sub_lbl = QLabel("Automate scheduled bills, subscriptions, rents, and salaries with balanced double-entry journals.")
        sub_lbl.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Member Filter
        self.member_combo = QComboBox()
        self.member_combo.addItem("All Family Rules", None)
        members = FamilyService.get_all_members()
        for m in members:
            self.member_combo.addItem(f"👤 {m.name}", m.id)
        self.member_combo.currentIndexChanged.connect(self.load_data)
        self.member_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 6px; padding: 6px 12px; color: #f8fafc; font-size: 13px;
            }
        """)
        header_layout.addWidget(self.member_combo)

        # Process Due Button
        process_btn = QPushButton("⚡ Process Due Now")
        process_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f766e; color: white; font-weight: 600;
                padding: 8px 16px; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #0d9488; }
        """)
        process_btn.clicked.connect(self.process_due_now)
        header_layout.addWidget(process_btn)

        # Add Rule Button
        add_btn = QPushButton("+ New Recurring Rule")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; color: white; font-weight: 600;
                padding: 8px 16px; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        add_btn.clicked.connect(self.open_add_dialog)
        header_layout.addWidget(add_btn)

        self.layout.addLayout(header_layout)

        # KPI Summary Cards
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(16)
        self.layout.addLayout(self.kpi_layout)

        # Rules Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Rule Title", "Type", "Frequency", "Next Due Date",
            "Amount (₹)", "Category", "Account", "Status", "Actions"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        rec_widths = {0: 180, 1: 95, 2: 105, 3: 115, 4: 125, 5: 135, 6: 145, 7: 95, 8: 90}
        configure_fintech_table(self.table, stretch_col=0, col_widths=rec_widths)
        self.layout.addWidget(self.table)

        self.load_data()

    def open_add_dialog(self):
        dlg = RecurringRuleDialog(self)
        if dlg.exec():
            self.load_data()

    def process_due_now(self):
        count, created = RecurringService.process_due_rules()
        if count > 0:
            QMessageBox.information(
                self, "Processing Complete",
                f"Successfully generated {count} recurring transaction(s) with balanced ledger entries!"
            )
            self.load_data()
        else:
            QMessageBox.information(self, "Up to Date", "No pending recurring transactions are due for execution today.")

    def load_data(self):
        # Clear KPIs
        while self.kpi_layout.count():
            item = self.kpi_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        selected_member_id = self.member_combo.currentData()
        rules = RecurringService.get_all_rules(selected_member_id)

        # Calculate KPIs
        active_count = sum(1 for r in rules if r.is_active)
        monthly_expense_paise = 0
        monthly_income_paise = 0
        upcoming_7d_count = 0
        today = date.today()
        week_ahead = today + timedelta(days=7)

        for r in rules:
            if not r.is_active:
                continue

            if today <= r.next_due_date <= week_ahead:
                upcoming_7d_count += 1

            # Approximate monthly flow
            multiplier = 1.0
            if r.frequency == "Daily":
                multiplier = 30.0
            elif r.frequency == "Weekly":
                multiplier = 4.0
            elif r.frequency == "Monthly":
                multiplier = 1.0
            elif r.frequency == "Quarterly":
                multiplier = 1.0 / 3.0
            elif r.frequency == "Yearly":
                multiplier = 1.0 / 12.0

            monthly_val = int(round(r.amount_paise * multiplier))
            if r.transaction_type == TransactionType.EXPENSE.value:
                monthly_expense_paise += monthly_val
            else:
                monthly_income_paise += monthly_val

        self._add_kpi_card("Active Rules", f"{active_count} of {len(rules)}", "#38bdf8")
        self._add_kpi_card("Monthly Outflow", f"₹{monthly_expense_paise / 100:,.2f}", "#f43f5e")
        self._add_kpi_card("Monthly Inflow", f"₹{monthly_income_paise / 100:,.2f}", "#10b981")
        self._add_kpi_card("Due in Next 7 Days", f"{upcoming_7d_count} Payments", "#f59e0b")

        # Populate Table
        self.table.setRowCount(len(rules))
        for row, r in enumerate(rules):
            # Title
            self.table.setItem(row, 0, QTableWidgetItem(r.title))

            # Type
            type_item = QTableWidgetItem(r.transaction_type)
            type_item.setForeground(Qt.green if r.transaction_type == TransactionType.INCOME.value else Qt.red)
            self.table.setItem(row, 1, type_item)

            # Frequency
            self.table.setItem(row, 2, QTableWidgetItem(r.frequency))

            # Next Due Date
            due_str = r.next_due_date.strftime("%d-%m-%Y")
            self.table.setItem(row, 3, QTableWidgetItem(due_str))

            # Amount
            amt_item = QTableWidgetItem(f"₹{r.amount_paise / 100:,.2f}")
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, amt_item)

            # Category
            cat_name = r.category.name if r.category else "-"
            self.table.setItem(row, 5, QTableWidgetItem(cat_name))

            # Account
            acc_name = r.account.name if r.account else "-"
            self.table.setItem(row, 6, QTableWidgetItem(acc_name))

            # Status
            status_item = QTableWidgetItem("Active" if r.is_active else "Paused")
            status_item.setForeground(Qt.cyan if r.is_active else Qt.gray)
            self.table.setItem(row, 7, status_item)

            # Actions
            action_widget = QWidget()
            a_lay = QHBoxLayout(action_widget)
            a_lay.setContentsMargins(4, 2, 4, 2)
            a_lay.setSpacing(6)

            toggle_btn = QPushButton("Pause" if r.is_active else "Resume")
            toggle_btn.setStyleSheet("background-color: #334155; color: #f8fafc; padding: 2px 8px; border-radius: 4px; font-size: 11px;")
            toggle_btn.clicked.connect(lambda _, r_id=r.id: self.toggle_rule(r_id))
            a_lay.addWidget(toggle_btn)

            del_btn = QPushButton("✕")
            del_btn.setStyleSheet("background-color: #334155; color: #94a3b8; padding: 2px 8px; border-radius: 4px; font-weight: bold;")
            del_btn.clicked.connect(lambda _, r_id=r.id: self.delete_rule(r_id))
            a_lay.addWidget(del_btn)

            self.table.setCellWidget(row, 8, action_widget)

    def _add_kpi_card(self, title: str, value: str, val_color: str):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 14px;
            }
        """)
        lay = QVBoxLayout(card)
        lay.setSpacing(4)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600; text-transform: uppercase;")
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(f"color: {val_color}; font-size: 20px; font-weight: 700;")
        lay.addWidget(t_lbl)
        lay.addWidget(v_lbl)
        self.kpi_layout.addWidget(card)

    def toggle_rule(self, rule_id: int):
        success, msg, _ = RecurringService.toggle_rule(rule_id)
        if success:
            self.load_data()
        else:
            QMessageBox.critical(self, "Error", msg)

    def delete_rule(self, rule_id: int):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this recurring rule? Existing transactions will be preserved.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = RecurringService.delete_rule(rule_id)
            if success:
                self.load_data()
            else:
                QMessageBox.critical(self, "Error", msg)
