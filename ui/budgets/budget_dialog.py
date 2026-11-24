"""
Budget Creation & Edit Dialog
Allows allocating monthly/periodic budgets across categories with live sum preview.
"""
from typing import Dict, Optional
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QDateEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame, QSpinBox
)
from PySide6.QtCore import Qt, QDate
from core.category_service import CategoryService
from core.family_service import FamilyService
from core.budget_service import BudgetService

class BudgetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Budget")
        self.setFixedSize(580, 680)
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; color: #f8fafc; }
            QLabel { color: #94a3b8; font-size: 13px; font-weight: 500; }
            QLineEdit, QComboBox, QDateEdit, QSpinBox {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 6px; padding: 8px 12px; color: #f8fafc; font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus { border: 1px solid #0ea5e9; }
            QTableWidget {
                background-color: #1e293b; border: 1px solid #334155;
                gridline-color: #334155; color: #f8fafc; border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #0f172a; color: #94a3b8; padding: 6px;
                border: 1px solid #334155; font-weight: 600;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title_lbl = QLabel("New Expense Budget")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(title_lbl)

        # Name
        layout.addWidget(QLabel("Budget Name *"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. March 2026 Household Budget")
        layout.addWidget(self.name_input)

        # Member & Period Row
        row1 = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Budget Scope (Family Member)"))
        self.member_combo = QComboBox()
        self.member_combo.addItem("Entire Family (Shared)", None)
        members = FamilyService.get_all_members()
        for m in members:
            self.member_combo.addItem(f"{m.name} ({m.relation_type})", m.id)
        v1.addWidget(self.member_combo)
        row1.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Period Type"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Monthly", "Quarterly", "Annual", "Custom"])
        v2.addWidget(self.period_combo)
        row1.addLayout(v2)
        layout.addLayout(row1)

        # Dates Row
        row2 = QHBoxLayout()
        v3 = QVBoxLayout()
        v3.addWidget(QLabel("Start Date"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        today = date.today()
        first_of_month = date(today.year, today.month, 1)
        self.start_date_edit.setDate(QDate(first_of_month.year, first_of_month.month, first_of_month.day))
        v3.addWidget(self.start_date_edit)
        row2.addLayout(v3)

        v4 = QVBoxLayout()
        v4.addWidget(QLabel("End Date"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        # End of current month
        import calendar
        _, last_day = calendar.monthrange(today.year, today.month)
        self.end_date_edit.setDate(QDate(today.year, today.month, last_day))
        v4.addWidget(self.end_date_edit)
        row2.addLayout(v4)
        layout.addLayout(row2)

        # Total Amount
        layout.addWidget(QLabel("Total Budget Cap (₹) *"))
        self.total_input = QLineEdit()
        self.total_input.setPlaceholderText("e.g. 50000")
        layout.addWidget(self.total_input)

        # Category Allocations
        layout.addWidget(QLabel("Category Allocations (Optional breakdown)"))
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(2)
        self.category_table.setHorizontalHeaderLabels(["Category", "Allocated (₹)"])
        self.category_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.category_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.populate_categories()
        layout.addWidget(self.category_table)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #334155; color: #f8fafc; padding: 9px 18px; border-radius: 6px;")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Create Budget")
        save_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: 600; padding: 9px 18px; border-radius: 6px;")
        save_btn.clicked.connect(self.save)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def populate_categories(self):
        categories = CategoryService.get_categories_by_type("Expense")
        self.category_table.setRowCount(len(categories))
        for row, cat in enumerate(categories):
            name_item = QTableWidgetItem(cat.name)
            name_item.setData(Qt.UserRole, cat.id)
            name_item.setFlags(name_item.flags() ^ Qt.ItemIsEditable)
            self.category_table.setItem(row, 0, name_item)

            amt_item = QTableWidgetItem("0")
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.category_table.setItem(row, 1, amt_item)

    def save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Budget name cannot be empty.")
            return

        try:
            total_rupees = float(self.total_input.text().strip() or "0")
            if total_rupees <= 0:
                raise ValueError()
            total_paise = int(round(total_rupees * 100))
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid positive budget amount.")
            return

        period_type = self.period_combo.currentText()
        member_id = self.member_combo.currentData()
        s_qdate = self.start_date_edit.date()
        e_qdate = self.end_date_edit.date()
        start_d = date(s_qdate.year(), s_qdate.month(), s_qdate.day())
        end_d = date(e_qdate.year(), e_qdate.month(), e_qdate.day())

        allocations: Dict[int, int] = {}
        for row in range(self.category_table.rowCount()):
            cat_id = self.category_table.item(row, 0).data(Qt.UserRole)
            amt_text = self.category_table.item(row, 1).text().strip()
            try:
                amt_val = float(amt_text)
                if amt_val > 0:
                    allocations[cat_id] = int(round(amt_val * 100))
            except ValueError:
                pass

        success, msg, _ = BudgetService.create_budget(
            name=name,
            period_type=period_type,
            start_date=start_d,
            end_date=end_d,
            total_budget_paise=total_paise,
            category_allocations=allocations,
            family_member_id=member_id
        )

        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to create budget: {msg}")
