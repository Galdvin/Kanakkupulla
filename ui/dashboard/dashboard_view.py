"""
Main Dashboard View:
- 10 KPI Summary Cards
- Date Range quick-filter pills (This Month, Last Month, This Year, etc.)
- Category-wise Expense distribution
- User/Family Member Spending distribution
- Payment Mode breakdown
"""
from datetime import date, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QComboBox, QPushButton, QScrollArea, QProgressBar
)
from PySide6.QtCore import Qt
from analytics.expense_analysis import AnalyticsService
from core.financial_utils import format_inr

class KPICard(QFrame):
    def __init__(self, title: str, initial_value: str = "₹0.00", subtitle: str = "", accent_color: str = "#38bdf8"):
        super().__init__()
        self.setProperty("class", "Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setProperty("class", "CardTitle")
        layout.addWidget(t_lbl)

        self.val_lbl = QLabel(initial_value)
        self.val_lbl.setProperty("class", "CardValue")
        self.val_lbl.setStyleSheet(f"color: {accent_color};")
        layout.addWidget(self.val_lbl)

        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.sub_lbl)

    def update_value(self, value_text: str, subtitle_text: str = ""):
        self.val_lbl.setText(value_text)
        if subtitle_text:
            self.sub_lbl.setText(subtitle_text)


class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # Header with Period Selector
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Financial Dashboard & Overview")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #38bdf8;")
        sub = QLabel("Real-time personal and family net worth, cash flow, and spending insights")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        header.addWidget(QLabel("Period:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "This Month", "Last Month", "Last 3 Months", "Last 6 Months", "This Year", "All Time"
        ])
        self.period_combo.currentIndexChanged.connect(self.load_data)
        header.addWidget(self.period_combo)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        header.addWidget(refresh_btn)
        root.addLayout(header)

        # Scroll Area for KPI Grid and Distribution widgets
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setSpacing(16)

        # 1. KPI Cards Grid (4 columns)
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(12)

        self.card_income = KPICard("Total Income", "₹0.00", "Selected period", "#10b981")
        self.card_expense = KPICard("Total Expenses", "₹0.00", "Selected period", "#ef4444")
        self.card_savings = KPICard("Net Savings", "₹0.00", "Income - Expenses", "#38bdf8")
        self.card_balance = KPICard("Current Liquid Balance", "₹0.00", "All active accounts", "#f59e0b")

        self.card_budget = KPICard("Monthly Budget", "₹0.00", "Allocated plan", "#a855f7")
        self.card_utilization = KPICard("Budget Utilization", "0.0%", "Spent percentage", "#ec4899")
        self.card_investments = KPICard("Total Investments", "₹0.00", "Portfolio valuation", "#06b6d4")
        self.card_loans = KPICard("Outstanding Loans", "₹0.00", "Active principal", "#f43f5e")

        kpi_grid.addWidget(self.card_income, 0, 0)
        kpi_grid.addWidget(self.card_expense, 0, 1)
        kpi_grid.addWidget(self.card_savings, 0, 2)
        kpi_grid.addWidget(self.card_balance, 0, 3)

        kpi_grid.addWidget(self.card_budget, 1, 0)
        kpi_grid.addWidget(self.card_utilization, 1, 1)
        kpi_grid.addWidget(self.card_investments, 1, 2)
        kpi_grid.addWidget(self.card_loans, 1, 3)

        scroll_layout.addLayout(kpi_grid)

        # 2. Category & Member Spending Breakdown Cards
        breakdown_layout = QHBoxLayout()

        # Category Box
        self.cat_box = QFrame()
        self.cat_box.setProperty("class", "Card")
        cat_inner = QVBoxLayout(self.cat_box)
        cat_title = QLabel("Top Category Expenses")
        cat_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #38bdf8;")
        cat_inner.addWidget(cat_title)
        self.cat_list_layout = QVBoxLayout()
        cat_inner.addLayout(self.cat_list_layout)
        breakdown_layout.addWidget(self.cat_box)

        # User / Member Box
        self.user_box = QFrame()
        self.user_box.setProperty("class", "Card")
        user_inner = QVBoxLayout(self.user_box)
        user_title = QLabel("Member Spending Distribution")
        user_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #38bdf8;")
        user_inner.addWidget(user_title)
        self.user_list_layout = QVBoxLayout()
        user_inner.addLayout(self.user_list_layout)
        breakdown_layout.addWidget(self.user_box)

        scroll_layout.addLayout(breakdown_layout)

        scroll.setWidget(container)
        root.addWidget(scroll)

    def get_date_range(self) -> tuple[date, date]:
        period = self.period_combo.currentText()
        today = date.today()
        if period == "This Month":
            return date(today.year, today.month, 1), today
        elif period == "Last Month":
            first_this_month = date(today.year, today.month, 1)
            last_month_end = first_this_month - timedelta(days=1)
            return date(last_month_end.year, last_month_end.month, 1), last_month_end
        elif period == "Last 3 Months":
            return today - timedelta(days=90), today
        elif period == "Last 6 Months":
            return today - timedelta(days=180), today
        elif period == "This Year":
            return date(today.year, 1, 1), today
        else: # All Time
            return date(2000, 1, 1), today

    def load_data(self):
        start_date, end_date = self.get_date_range()
        metrics = AnalyticsService.get_dashboard_metrics(start_date, end_date)

        # Update KPI Cards
        self.card_income.update_value(format_inr(metrics["total_income_paise"]))
        self.card_expense.update_value(format_inr(metrics["total_expense_paise"]))
        self.card_savings.update_value(format_inr(metrics["total_savings_paise"]))
        self.card_balance.update_value(format_inr(metrics["current_balance_paise"]))

        self.card_budget.update_value(format_inr(metrics["monthly_budget_paise"]))
        self.card_utilization.update_value(f"{metrics['budget_utilization_pct']}%")
        self.card_investments.update_value(format_inr(metrics["total_investments_paise"]))
        self.card_loans.update_value(format_inr(metrics["total_loans_paise"]))

        # Populate Category Bars
        self._clear_layout(self.cat_list_layout)
        cats = metrics["category_distribution"][:6] # Top 6
        total_exp = metrics["total_expense_paise"] or 1
        if not cats:
            lbl = QLabel("No expense data recorded in this period.")
            lbl.setStyleSheet("color: #64748b; font-style: italic;")
            self.cat_list_layout.addWidget(lbl)
        else:
            for c in cats:
                pct = int(round(c["amount_paise"] / total_exp * 100))
                row = QVBoxLayout()
                header = QHBoxLayout()
                header.addWidget(QLabel(c["name"]))
                amt = QLabel(f"{format_inr(c['amount_paise'])} ({pct}%)")
                amt.setStyleSheet("font-weight: 600; color: #f8fafc;")
                header.addStretch()
                header.addWidget(amt)
                row.addLayout(header)

                pbar = QProgressBar()
                pbar.setFixedHeight(8)
                pbar.setTextVisible(False)
                pbar.setValue(min(100, pct))
                pbar.setStyleSheet("QProgressBar::chunk { background-color: #38bdf8; border-radius: 4px; }")
                row.addWidget(pbar)
                self.cat_list_layout.addLayout(row)

        # Populate User/Member Bars
        self._clear_layout(self.user_list_layout)
        users = metrics["user_distribution"]
        if not users:
            lbl = QLabel("No member expense recorded in this period.")
            lbl.setStyleSheet("color: #64748b; font-style: italic;")
            self.user_list_layout.addWidget(lbl)
        else:
            for u in users:
                pct = int(round(u["amount_paise"] / total_exp * 100))
                row = QVBoxLayout()
                header = QHBoxLayout()
                header.addWidget(QLabel(u["user"]))
                amt = QLabel(f"{format_inr(u['amount_paise'])} ({pct}%)")
                amt.setStyleSheet("font-weight: 600; color: #10b981;")
                header.addStretch()
                header.addWidget(amt)
                row.addLayout(header)

                pbar = QProgressBar()
                pbar.setFixedHeight(8)
                pbar.setTextVisible(False)
                pbar.setValue(min(100, pct))
                pbar.setStyleSheet("QProgressBar::chunk { background-color: #10b981; border-radius: 4px; }")
                row.addWidget(pbar)
                self.user_list_layout.addLayout(row)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
