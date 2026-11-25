"""
Master Dashboard View (Version 2.0 - Family Finance Platform)
Displays:
1. Two Viewing Modes:
   - "Family Overview" (Consolidated family finances)
   - "Individual Member Overview" (Selected member's individual finances)
2. 8 Core KPI Cards:
   - Total Family Income
   - Total Family Expenses
   - Total Family Savings
   - Available Bank Balance
   - Monthly Budget Remaining
   - Total Investments
   - Total Liabilities
   - Family Net Worth
3. Interactive category and member breakdowns
"""
from datetime import date, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QComboBox, QPushButton, QScrollArea, QProgressBar
)
from PySide6.QtCore import Qt
from analytics.expense_analysis import AnalyticsService
from core.family_service import FamilyService
from core.financial_utils import format_inr
from ui.dashboard.dashboard_view import KPICard

class MasterFamilyDashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # Header Bar with Viewing Mode & Period
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Family Financial Intelligence")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #14b8a6;")
        sub = QLabel("Family net worth, cash flow & member financial positions")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        # Viewing Mode Selector: Family Consolidated vs Individual Member
        header.addWidget(QLabel("View Mode:"))
        self.member_combo = QComboBox()
        self.member_combo.addItem("👨‍👩‍👧‍👦 Family Overview (Consolidated)", None)
        for m in FamilyService.get_all_members():
            self.member_combo.addItem(f"👤 {m.name} ({m.relation_type})", m.id)
        self.member_combo.currentIndexChanged.connect(self.load_data)
        header.addWidget(self.member_combo)

        # Period Filter
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

        # Scroll Area for 8 KPI Cards Grid & Distributions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setSpacing(16)

        # 8 KPI Cards Grid (4 columns x 2 rows)
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(12)

        self.card_income = KPICard("Total Family Income", "₹0.00", "Posted income", "#10b981")
        self.card_expense = KPICard("Total Family Expenses", "₹0.00", "Net of refunds", "#ef4444")
        self.card_savings = KPICard("Total Family Savings", "₹0.00", "Income - Expenses", "#14b8a6")
        self.card_balance = KPICard("Available Bank Balance", "₹0.00", "All liquid accounts", "#38bdf8")

        self.card_budget = KPICard("Monthly Budget Remaining", "₹0.00", "Allocated plan", "#a855f7")
        self.card_investments = KPICard("Total Investments", "₹0.00", "Current valuation", "#06b6d4")
        self.card_liabilities = KPICard("Total Liabilities", "₹0.00", "Loans & Cards", "#f43f5e")
        self.card_net_worth = KPICard("Family Net Worth", "₹0.00", "Assets - Liabilities", "#f59e0b")

        kpi_grid.addWidget(self.card_income, 0, 0)
        kpi_grid.addWidget(self.card_expense, 0, 1)
        kpi_grid.addWidget(self.card_savings, 0, 2)
        kpi_grid.addWidget(self.card_balance, 0, 3)

        kpi_grid.addWidget(self.card_budget, 1, 0)
        kpi_grid.addWidget(self.card_investments, 1, 1)
        kpi_grid.addWidget(self.card_liabilities, 1, 2)
        kpi_grid.addWidget(self.card_net_worth, 1, 3)

        scroll_layout.addLayout(kpi_grid)

        # Bottom Distribution Panels (Category vs Payer/Beneficiary)
        breakdown_layout = QHBoxLayout()

        # Category Box
        cat_box = QFrame()
        cat_box.setProperty("class", "Card")
        cat_inner = QVBoxLayout(cat_box)
        cat_title = QLabel("Category Spending")
        cat_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #14b8a6;")
        cat_inner.addWidget(cat_title)
        self.cat_list_layout = QVBoxLayout()
        cat_inner.addLayout(self.cat_list_layout)
        breakdown_layout.addWidget(cat_box)

        # Payer vs Beneficiary Box
        member_box = QFrame()
        member_box.setProperty("class", "Card")
        member_inner = QVBoxLayout(member_box)
        member_title = QLabel("Member Spending Attribution")
        member_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #14b8a6;")
        member_inner.addWidget(member_title)
        self.member_list_layout = QVBoxLayout()
        member_inner.addLayout(self.member_list_layout)
        breakdown_layout.addWidget(member_box)

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
        else:
            return date(2000, 1, 1), today

    def load_data(self):
        start_date, end_date = self.get_date_range()
        selected_member_id = self.member_combo.currentData()

        metrics = AnalyticsService.get_dashboard_metrics(
            start_date=start_date,
            end_date=end_date,
            filter_member_id=selected_member_id
        )

        is_individual = selected_member_id is not None
        prefix = "Individual" if is_individual else "Family"

        # Update 8 KPI Cards
        self.card_income.update_value(format_inr(metrics["total_income_paise"]))
        self.card_expense.update_value(format_inr(metrics["total_expense_paise"]))
        self.card_savings.update_value(format_inr(metrics["total_savings_paise"]), f"Savings Rate: {metrics['savings_rate_pct']}%")
        self.card_balance.update_value(format_inr(metrics["liquid_balance_paise"]))

        self.card_budget.update_value(format_inr(metrics["budget_remaining_paise"]), f"{metrics['budget_utilization_pct']}% Utilized")
        self.card_investments.update_value(format_inr(metrics["total_investments_paise"]))
        self.card_liabilities.update_value(format_inr(metrics["total_liabilities_paise"]))
        self.card_net_worth.update_value(format_inr(metrics["family_net_worth_paise"]))

        # Categories
        self._clear_layout(self.cat_list_layout)
        cats = metrics["category_distribution"][:6]
        total_exp = metrics["total_expense_paise"] or 1
        if not cats:
            lbl = QLabel("No expenses recorded in this period.")
            lbl.setStyleSheet("color: #64748b; font-style: italic;")
            self.cat_list_layout.addWidget(lbl)
        else:
            for c in cats:
                pct = int(round(c["amount_paise"] / total_exp * 100))
                row = QVBoxLayout()
                h = QHBoxLayout()
                h.addWidget(QLabel(c["name"]))
                amt = QLabel(f"{format_inr(c['amount_paise'])} ({pct}%)")
                amt.setStyleSheet("font-weight: 600; color: #f8fafc;")
                h.addStretch()
                h.addWidget(amt)
                row.addLayout(h)

                pbar = QProgressBar()
                pbar.setFixedHeight(8)
                pbar.setTextVisible(False)
                pbar.setValue(min(100, pct))
                pbar.setStyleSheet("QProgressBar::chunk { background-color: #0d9488; border-radius: 4px; }")
                row.addWidget(pbar)
                self.cat_list_layout.addLayout(row)

        # Member Distribution
        self._clear_layout(self.member_list_layout)
        payers = metrics["user_distribution"]
        if not payers:
            lbl = QLabel("No member expense recorded in this period.")
            lbl.setStyleSheet("color: #64748b; font-style: italic;")
            self.member_list_layout.addWidget(lbl)
        else:
            for p in payers:
                pct = int(round(p["amount_paise"] / total_exp * 100))
                row = QVBoxLayout()
                h = QHBoxLayout()
                h.addWidget(QLabel(f"Paid by: {p['user']}"))
                amt = QLabel(f"{format_inr(p['amount_paise'])} ({pct}%)")
                amt.setStyleSheet("font-weight: 600; color: #10b981;")
                h.addStretch()
                h.addWidget(amt)
                row.addLayout(h)

                pbar = QProgressBar()
                pbar.setFixedHeight(8)
                pbar.setTextVisible(False)
                pbar.setValue(min(100, pct))
                pbar.setStyleSheet("QProgressBar::chunk { background-color: #10b981; border-radius: 4px; }")
                row.addWidget(pbar)
                self.member_list_layout.addLayout(row)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
