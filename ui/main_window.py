"""
Main Window Shell for Kanakkupulla
Features:
- Modern sleek sidebar navigation
- Dynamic Page switching with QStackedWidget
- Top status bar with active user profile, theme switcher, and logout
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QStackedWidget, QFrame, QButtonGroup, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont

from assets.styles.fintech_theme import FINTECH_DARK_THEME
from assets.styles.theme import LIGHT_THEME
from core.authentication import AuthService
from ui.dashboard.master_dashboard_view import MasterFamilyDashboardView
from ui.users.users_view import UsersView
from ui.expenses.expenses_view import ExpensesView
from ui.income.income_view import IncomeView
from ui.accounts.accounts_view import AccountsView
from ui.accounts.general_ledger_view import GeneralLedgerView
from ui.analytics.net_worth_view import NetWorthView
from ui.analytics.heatmap_view import HeatmapView
from ui.analytics.subscription_view import SubscriptionView
from ui.budgets.budgets_view import BudgetsView
from ui.savings.savings_view import SavingsView
from ui.investments.investments_view import InvestmentsView
from ui.loans.loans_view import LoansView
from ui.recurring.recurring_view import RecurringView
from ui.calendar.calendar_view import CalendarView
from ui.planning.financial_planning_view import FinancialPlanningView
from config.constants import ExpenseKind

class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.setWindowTitle("Kanakkupulla - Personal Finance & Analytics")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 680)
        self.is_dark_mode = True
        self.setStyleSheet(FINTECH_DARK_THEME)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar
        sidebar = self.create_sidebar()
        root_layout.addWidget(sidebar)

        # 2. Main Content Area
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top Header Bar
        top_bar = self.create_top_bar()
        content_layout.addWidget(top_bar)

        # Stacked Pages
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        root_layout.addWidget(content_container, stretch=1)

        # Populate Initial Pages
        self.init_pages()

        # Select Dashboard by default
        if hasattr(self, "nav_btns") and self.nav_btns:
            self.nav_btns[0].click()

    def create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(240)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(6)

        # Branding
        brand_layout = QHBoxLayout()
        logo_lbl = QLabel("Kanakkupulla")
        logo_lbl.setObjectName("LogoText")
        brand_layout.addWidget(logo_lbl)
        layout.addLayout(brand_layout)

        layout.addSpacing(15)

        # Navigation Buttons
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_btns = []

        nav_items = [
            ("Dashboard", 0),
            ("Daily Expenses", 1),
            ("Other Expenses", 2),
            ("Income", 3),
            ("Accounts & Cards", 4),
            ("General Ledger", 5),
            ("Net Worth Tracker", 6),
            ("Spending Heatmap", 7),
            ("Subscriptions", 8),
            ("Budgets", 9),
            ("Savings Goals", 10),
            ("Investments", 11),
            ("Loans & EMIs", 12),
            ("Recurring Rules", 13),
            ("Financial Calendar", 14),
            ("Financial Planning", 15),
            ("Reports & Analytics", 16),
            ("Users & Family", 17),
        ]

        for text, page_idx in nav_items:
            btn = QPushButton(text)
            btn.setProperty("class", "NavBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=page_idx: self.switch_page(idx))
            self.nav_group.addButton(btn)
            self.nav_btns.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Version & Offline status footer
        footer_lbl = QLabel("v1.0.0 (Offline Mode)")
        footer_lbl.setStyleSheet("color: #64748b; font-size: 11px; padding-left: 10px;")
        layout.addWidget(footer_lbl)

        return sidebar

    def create_top_bar(self) -> QFrame:
        top_bar = QFrame()
        top_bar.setFixedHeight(56)
        top_bar.setStyleSheet("border-bottom: 1px solid #334155; background-color: #1e293b;")
        
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 0, 20, 0)

        # Title / Breadcrumb
        self.page_title = QLabel("Dashboard")
        self.page_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc;")
        layout.addWidget(self.page_title)

        layout.addStretch()

        # Theme toggle button
        self.theme_btn = QPushButton("Toggle Theme")
        self.theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_btn)

        # Active user badge
        user_name = self.current_user.full_name if self.current_user else "User"
        user_role = (self.current_user.role if self.current_user else "standard").capitalize()
        user_badge = QLabel(f"👤 {user_name} ({user_role})")
        user_badge.setStyleSheet("color: #38bdf8; font-weight: 600; padding: 0 10px;")
        layout.addWidget(user_badge)

        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setProperty("class", "DangerBtn")
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)

        return top_bar

    def init_pages(self):
        # 0: Master Dashboard (Family and Individual Viewing Modes)
        self.dashboard_view = MasterFamilyDashboardView()
        self.stack.addWidget(self.dashboard_view)

        # 1: Daily Expenses
        self.daily_expenses_view = ExpensesView(expense_kind=ExpenseKind.DAILY.value)
        self.stack.addWidget(self.daily_expenses_view)

        # 2: Other Expenses
        self.other_expenses_view = ExpensesView(expense_kind=ExpenseKind.OCCASIONAL.value)
        self.stack.addWidget(self.other_expenses_view)

        # 3: Income
        self.income_view = IncomeView()
        self.stack.addWidget(self.income_view)

        # 4: Accounts
        self.accounts_view = AccountsView()
        self.stack.addWidget(self.accounts_view)

        # 5: General Ledger
        self.general_ledger_view = GeneralLedgerView()
        self.stack.addWidget(self.general_ledger_view)

        # 6: Net Worth Tracker
        self.net_worth_view = NetWorthView()
        self.stack.addWidget(self.net_worth_view)

        # 6: Spending Heatmap
        self.heatmap_view = HeatmapView()
        self.stack.addWidget(self.heatmap_view)

        # 8: Subscriptions
        self.subscription_view = SubscriptionView()
        self.stack.addWidget(self.subscription_view)

        # 9: Budgets
        self.budgets_view = BudgetsView()
        self.stack.addWidget(self.budgets_view)

        # 10: Savings
        self.savings_view = SavingsView()
        self.stack.addWidget(self.savings_view)

        # 11: Investments
        self.investments_view = InvestmentsView()
        self.stack.addWidget(self.investments_view)

        # 12: Loans & EMIs
        self.loans_view = LoansView()
        self.stack.addWidget(self.loans_view)

        # 13: Recurring Rules
        self.recurring_view = RecurringView()
        self.stack.addWidget(self.recurring_view)

        # 14: Financial Calendar
        self.calendar_view = CalendarView()
        self.stack.addWidget(self.calendar_view)

        # 15: Financial Planning
        self.planning_view = FinancialPlanningView()
        self.stack.addWidget(self.planning_view)

        # 16: Reports & Analytics
        self.reports_placeholder = self._create_placeholder_page("Comprehensive Reports & Analytics")
        self.stack.addWidget(self.reports_placeholder)

        # 17: Users & Family
        self.users_view = UsersView()
        self.stack.addWidget(self.users_view)

        # 13: Settings
        self.settings_placeholder = self._create_placeholder_page("Application Settings & Backups")
        self.stack.addWidget(self.settings_placeholder)

    def _create_placeholder_page(self, title_text: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel(title_text)
        lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #64748b;")
        layout.addWidget(lbl)
        return widget

    def switch_page(self, idx: int):
        self.stack.setCurrentIndex(idx)
        titles = [
            "Dashboard", "Daily Expenses", "Other Expenses", "Income",
            "Accounts & Cards", "General Ledger", "Net Worth Tracker",
            "Spending Heatmap", "Subscriptions", "Budgets", "Savings Goals",
            "Investments", "Loans & EMIs", "Recurring Rules", "Financial Calendar",
            "Financial Planning", "Reports & Analytics", "Users & Family"
        ]
        if idx < len(titles):
            self.page_title.setText(titles[idx])

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.setStyleSheet(FINTECH_DARK_THEME)
        else:
            self.setStyleSheet(LIGHT_THEME)

    def logout(self):
        reply = QMessageBox.question(
            self, "Logout", "Are you sure you want to sign out?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            AuthService.logout()
            self.close()
