"""
Daily Expenses View:
Comprehensive table of daily expenses with search, date filters, user/category filters,
and quick actions to add, delete, and duplicate transactions.
"""
from datetime import date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
    QLineEdit, QDateEdit, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QDate
from core.expense_service import ExpenseService
from core.category_service import CategoryService
from core.family_service import FamilyService
from core.transaction_search_service import TransactionSearchService
from core.financial_utils import format_inr, format_date
from config.constants import ExpenseKind
from ui.expenses.expense_dialog import ExpenseEntryDialog
from ui.expenses.quick_expense_dialog import QuickExpenseDialog
from ui.expenses.receipt_scanner_dialog import SmartReceiptDialog

class ExpensesView(QWidget):
    def __init__(self, expense_kind: str = ExpenseKind.DAILY.value, parent=None):
        super().__init__(parent)
        self.expense_kind = expense_kind
        self.init_ui()
        self.load_expenses()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # 1. Header Bar
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Daily Expenses" if self.expense_kind == ExpenseKind.DAILY.value else "Occasional / Other Expenses")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #38bdf8;")
        sub = QLabel("Track, search, and manage spending across family members and categories")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.quick_add_btn = QPushButton("⚡ Quick Entry")
        self.quick_add_btn.setStyleSheet("background-color: #0d9488; font-weight: 700; color: #ffffff; border-radius: 6px; padding: 6px 14px;")
        self.quick_add_btn.clicked.connect(self.open_quick_dialog)
        header.addWidget(self.quick_add_btn)

        scan_btn = QPushButton("📷 Scan Bill / Receipt")
        scan_btn.clicked.connect(self.open_scan_dialog)
        header.addWidget(scan_btn)

        self.add_btn = QPushButton(f"+ Add {title.text()}")
        self.add_btn.setProperty("class", "PrimaryBtn")
        self.add_btn.clicked.connect(self.open_add_dialog)
        header.addWidget(self.add_btn)
        layout.addLayout(header)

        # 2. Filter & Search Bar
        filter_card = QFrame()
        filter_card.setProperty("class", "Card")
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(12, 10, 12, 10)
        filter_layout.setSpacing(10)

        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search title, shop, ref...")
        self.search_input.textChanged.connect(self.load_expenses)
        filter_layout.addWidget(self.search_input)

        filter_layout.addWidget(QLabel("Category:"))
        self.cat_filter = QComboBox()
        self.cat_filter.addItem("All Categories", None)
        for c in CategoryService.get_all_categories():
            self.cat_filter.addItem(c.name, c.id)
        self.cat_filter.currentIndexChanged.connect(self.load_expenses)
        filter_layout.addWidget(self.cat_filter)

        filter_layout.addWidget(QLabel("Paid By:"))
        self.user_filter = QComboBox()
        self.user_filter.addItem("All Members", None)
        for m in FamilyService.get_all_members():
            self.user_filter.addItem(f"{m.name} ({m.relation_type})", m.id)
        self.user_filter.currentIndexChanged.connect(self.load_expenses)
        filter_layout.addWidget(self.user_filter)

        filter_layout.addStretch()

        self.total_lbl = QLabel("Total: ₹0.00")
        self.total_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #10b981;")
        filter_layout.addWidget(self.total_lbl)

        layout.addWidget(filter_card)

        # 3. Expenses Table
        self.table = QTableWidget()
        headers = ["ID", "Date", "Title", "Category", "Paid By", "Expense For", "Account / Mode", "Attachments", "Amount"]
        if self.expense_kind == ExpenseKind.OCCASIONAL.value:
            headers.insert(3, "Event / Occasion")

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        # 4. Action buttons bar
        actions_bar = QHBoxLayout()
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setProperty("class", "DangerBtn")
        delete_btn.clicked.connect(self.delete_selected)
        actions_bar.addWidget(delete_btn)

        actions_bar.addStretch()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_expenses)
        actions_bar.addWidget(refresh_btn)
        layout.addLayout(actions_bar)

    def load_expenses(self):
        cat_id = self.cat_filter.currentData()
        member_id = self.user_filter.currentData()
        kw = self.search_input.text().strip() if hasattr(self, "search_input") else None

        expenses, count, total_paise = TransactionSearchService.search_transactions(
            keyword=kw,
            category_id=cat_id,
            paid_by_member_id=member_id,
            expense_kind=self.expense_kind,
            transaction_type="Expense",
            limit=250
        )

        self.table.setRowCount(len(expenses))

        for row, txn in enumerate(expenses):
            col = 0
            
            # ID
            id_item = QTableWidgetItem(str(txn.id))
            id_item.setData(Qt.UserRole, txn.id)
            self.table.setItem(row, col, id_item); col += 1

            # Date
            self.table.setItem(row, col, QTableWidgetItem(format_date(txn.transaction_date))); col += 1

            # Title
            self.table.setItem(row, col, QTableWidgetItem(txn.title)); col += 1

            # Event (if Occasional)
            if self.expense_kind == ExpenseKind.OCCASIONAL.value:
                self.table.setItem(row, col, QTableWidgetItem(txn.event_name or "-")); col += 1

            # Category
            cat_name = txn.category.name if txn.category else "Uncategorized"
            self.table.setItem(row, col, QTableWidgetItem(cat_name)); col += 1

            # Paid By
            self.table.setItem(row, col, QTableWidgetItem(txn.paid_by_member.name if txn.paid_by_member else "-")); col += 1

            # Expense For
            self.table.setItem(row, col, QTableWidgetItem(txn.expense_for_member.name if txn.expense_for_member else "-")); col += 1

            # Account / Mode
            acc_info = f"{txn.account.name if txn.account else ''} ({txn.payment_method})"
            self.table.setItem(row, col, QTableWidgetItem(acc_info)); col += 1

            # Attachments
            att_count = len(txn.attachments)
            att_str = f"📎 {att_count}" if att_count > 0 else "-"
            self.table.setItem(row, col, QTableWidgetItem(att_str)); col += 1

            # Amount
            amt_item = QTableWidgetItem(format_inr(txn.amount_paise))
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, col, amt_item)

        self.total_lbl.setText(f"Total: {format_inr(total_paise)}")

    def open_quick_dialog(self):
        dlg = QuickExpenseDialog(parent=self)
        if dlg.exec():
            self.load_expenses()

    def open_scan_dialog(self):
        dlg = SmartReceiptDialog(parent=self)
        if dlg.exec():
            self.load_expenses()

    def open_add_dialog(self):
        dlg = ExpenseEntryDialog(expense_kind=self.expense_kind, parent=self)
        if dlg.exec():
            self.load_expenses()

    def delete_selected(self):
        curr_row = self.table.currentRow()
        if curr_row < 0:
            QMessageBox.information(self, "Selection", "Please select an expense to delete.")
            return

        txn_id = self.table.item(curr_row, 0).data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Confirm Delete", "Are you sure you want to delete this expense? Account balance will be restored.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            ok, msg = ExpenseService.delete_expense(txn_id)
            if ok:
                self.load_expenses()
            else:
                QMessageBox.critical(self, "Error", msg)
