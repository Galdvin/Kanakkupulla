"""
Main Window Shell for Kanakkupulla
Features:
- Sleek palette-driven QListWidget sidebar navigation based on CameronBrooks11/pyside6-gui-template
- Dynamic Page switching with QStackedWidget
- Top status bar with active user profile, theme switcher, and logout
- Geometry and theme persistence with QSettings
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QStackedWidget, QFrame, QMessageBox, QListWidget, QListWidgetItem,
    QAbstractItemView, QStyledItemDelegate
)
from PySide6.QtCore import Qt, QSize, QSettings, QByteArray, QEvent
from PySide6.QtGui import QIcon, QFont, QCloseEvent, QPixmap

from core.theme_manager import apply_app_theme, dark_palette, light_palette, DARK, LIGHT
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
from ui.reports.reports_view import ReportsView
from ui.settings.settings_view import SettingsView
from config.constants import ExpenseKind

NAV_ICONS_DIR = Path(__file__).parent.parent / "assets" / "icons" / "nav"
APP_LOGO_PATH = Path(__file__).parent.parent / "assets" / "icons" / "app_logo.svg"

# Palette-driven Navigation Style (Clean modern fintech design)
NAVIGATION_STYLE = """
QListWidget#SidebarNav {
    background-color: transparent;
    border: none;
    outline: none;
    padding: 2px 4px;
}
QListWidget#SidebarNav::item {
    height: 32px;
    border-radius: 6px;
    padding-left: 10px;
    padding-right: 10px;
    margin: 1px 4px;
    color: #94a3b8;
    font-size: 13px;
    font-weight: 500;
    border: none;
}
QListWidget#SidebarNav::item:hover {
    background-color: #1e293b;
    color: #f1f5f9;
}
QListWidget#SidebarNav::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(15, 118, 110, 0.75), stop:1 rgba(20, 184, 166, 0.25));
    color: #ffffff;
    font-weight: 600;
    border-left: 3px solid #2dd4bf;
    border-radius: 6px;
}
QListWidget#SidebarNav QScrollBar:vertical {
    background: transparent;
    width: 4px;
    margin: 0px;
    border: none;
}
QListWidget#SidebarNav QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 2px;
}
QListWidget#SidebarNav QScrollBar::handle:vertical:hover {
    background: #14b8a6;
}
QListWidget#SidebarNav QScrollBar::add-line:vertical,
QListWidget#SidebarNav QScrollBar::sub-line:vertical,
QListWidget#SidebarNav QScrollBar::add-page:vertical,
QListWidget#SidebarNav QScrollBar::sub-page:vertical {
    background: transparent;
    border: none;
    height: 0px;
}
"""

class ModernNavDelegate(QStyledItemDelegate):
    """Delegate to suppress clumsy default elided text tooltips and ensure sleek rendering."""
    def helpEvent(self, event, view, option, index):
        # Suppress clumsy default elided text popups that float outside the sidebar
        return False


class NavBtnProxy:
    """Compatibility adapter for nav_btns in tests and existing callers."""
    def __init__(self, window, page_idx, list_item):
        self._window = window
        self._page_idx = page_idx
        self._item = list_item

    def click(self):
        self._window.switch_page(self._page_idx)

    def setChecked(self, checked: bool):
        if checked:
            self._window.navigation.setCurrentItem(self._item)

    def isChecked(self) -> bool:
        return self._window.navigation.currentItem() == self._item

    def isVisible(self) -> bool:
        return True

    def text(self) -> str:
        return self._item.text()


class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.setWindowTitle("Kanakkupulla - Personal Finance & Analytics")
        self.resize(1300, 820)
        self.setMinimumSize(1080, 700)
        self.is_dark_mode = True
        
        apply_app_theme(DARK)
        self.setStyleSheet(FINTECH_DARK_THEME)

        self.init_ui()

        # Restore window geometry
        geom = QSettings().value("geometry")
        if isinstance(geom, QByteArray):
            self.restoreGeometry(geom)

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
        if hasattr(self, "navigation") and self.navigation.count() > 0:
            self.navigation.setCurrentRow(0)

    def create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("background-color: #0d1322; border-right: 1px solid #1e293b;")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Brand Header
        brand_widget = QWidget()
        brand_layout = QVBoxLayout(brand_widget)
        brand_layout.setContentsMargins(18, 16, 18, 12)
        brand_layout.setSpacing(4)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        
        logo_icon = QLabel()
        if APP_LOGO_PATH.exists():
            logo_pixmap = QIcon(str(APP_LOGO_PATH)).pixmap(QSize(28, 28))
            logo_icon.setPixmap(logo_pixmap)
        logo_icon.setFixedSize(28, 28)
        brand_row.addWidget(logo_icon)

        logo_lbl = QLabel("Kanakkupulla")
        logo_lbl.setObjectName("LogoText")
        logo_lbl.setStyleSheet("font-size: 17px; font-weight: 800; color: #2dd4bf; letter-spacing: -0.2px;")
        brand_row.addWidget(logo_lbl)
        brand_row.addStretch()
        brand_layout.addLayout(brand_row)

        sub_lbl = QLabel("கணக்குப்புள்ள • Family Finance")
        sub_lbl.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 500; padding-left: 2px;")
        brand_layout.addWidget(sub_lbl)
        layout.addWidget(brand_widget)

        # Primary Action Button: + Quick Expense
        quick_btn_wrap = QWidget()
        quick_btn_layout = QVBoxLayout(quick_btn_wrap)
        quick_btn_layout.setContentsMargins(14, 4, 14, 10)
        quick_btn_layout.setSpacing(0)

        self.quick_add_btn = QPushButton("＋ Quick Expense")
        self.quick_add_btn.setObjectName("SidebarQuickExpenseBtn")
        self.quick_add_btn.setCursor(Qt.PointingHandCursor)
        self.quick_add_btn.setFixedHeight(36)
        self.quick_add_btn.setStyleSheet("""
            QPushButton#SidebarQuickExpenseBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f766e, stop:1 #14b8a6);
                color: #ffffff;
                font-weight: 700;
                font-size: 13px;
                border: 1px solid #2dd4bf;
                border-radius: 8px;
                padding: 0 12px;
            }
            QPushButton#SidebarQuickExpenseBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #14b8a6, stop:1 #2dd4bf);
                color: #0f172a;
                border-color: #5eead4;
            }
            QPushButton#SidebarQuickExpenseBtn:pressed {
                background: #0d9488;
                color: #ffffff;
            }
        """)
        self.quick_add_btn.clicked.connect(self.open_quick_expense)
        quick_btn_layout.addWidget(self.quick_add_btn)
        layout.addWidget(quick_btn_wrap)

        # Navigation List (CameronBrooks11 style with smooth pixel scroll)
        self.navigation = QListWidget()
        self.navigation.setObjectName("SidebarNav")
        self.navigation.setFrameShape(QFrame.Shape.NoFrame)
        self.navigation.setIconSize(QSize(18, 18))
        self.navigation.setStyleSheet(NAVIGATION_STYLE)
        self.navigation.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.navigation.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.navigation.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.navigation.setUniformItemSizes(True)
        self.navigation.setItemDelegate(ModernNavDelegate(self.navigation))

        nav_items = [
            ("dashboard.svg", "Dashboard", 0),
            ("expenses.svg", "Daily Expenses", 1),
            ("other_expenses.svg", "Other Expenses", 2),
            ("income.svg", "Income Management", 3),
            ("accounts.svg", "Accounts & Cards", 4),
            ("ledger.svg", "General Ledger", 5),
            ("net_worth.svg", "Net Worth Tracker", 6),
            ("heatmap.svg", "Spending Heatmap", 7),
            ("subscriptions.svg", "Subscription Tracker", 8),
            ("budgets.svg", "Budget Management", 9),
            ("savings.svg", "Savings Goals", 10),
            ("investments.svg", "Investments Portfolio", 11),
            ("loans.svg", "Loans & EMIs", 12),
            ("recurring.svg", "Recurring Rules", 13),
            ("calendar.svg", "Financial Calendar", 14),
            ("planning.svg", "Financial Planning", 15),
            ("reports.svg", "Reports & Analytics", 16),
            ("family.svg", "Users & Family", 17),
            ("settings.svg", "Settings & Backup", 18),
        ]

        self.nav_btns = []
        for icon_file, title, page_idx in nav_items:
            icon_path = NAV_ICONS_DIR / icon_file
            icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()
            item = QListWidgetItem(icon, title, self.navigation)
            item.setSizeHint(QSize(240, 32))
            item.setData(Qt.UserRole, page_idx)
            proxy = NavBtnProxy(self, page_idx, item)
            self.nav_btns.append(proxy)

        self.navigation.currentRowChanged.connect(self.switch_page)
        layout.addWidget(self.navigation, stretch=1)

        # Footer
        footer = QWidget()
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(16, 12, 16, 14)
        footer_layout.setSpacing(4)
        footer.setStyleSheet("border-top: 1px solid #1e293b; background-color: #090e1a;")

        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        dot = QLabel("🟢")
        dot.setStyleSheet("font-size: 9px;")
        status_row.addWidget(dot)

        offline_lbl = QLabel("100% Offline Database")
        offline_lbl.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 600;")
        status_row.addWidget(offline_lbl)
        status_row.addStretch()
        footer_layout.addLayout(status_row)

        ver_lbl = QLabel("Kanakkupulla v1.0 • SQLite WAL")
        ver_lbl.setStyleSheet("color: #475569; font-size: 10px; font-weight: 500;")
        footer_layout.addWidget(ver_lbl)

        layout.addWidget(footer)
        return sidebar

    def create_top_bar(self) -> QFrame:
        top_bar = QFrame()
        top_bar.setFixedHeight(56)
        top_bar.setStyleSheet("border-bottom: 1px solid #1e293b; background-color: #0d1322;")
        
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        # Title / Breadcrumb
        self.page_title = QLabel("Dashboard")
        self.page_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #f8fafc;")
        layout.addWidget(self.page_title)

        layout.addStretch()

        # Theme toggle button
        self.theme_btn = QPushButton("🌙 Dark")
        self.theme_btn.setFixedHeight(32)
        self.theme_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 0 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #f8fafc;
            }
        """)
        self.theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_btn)

        # Active user badge
        user_name = self.current_user.full_name if self.current_user else "User"
        user_role = (self.current_user.role if self.current_user else "standard").capitalize()
        user_badge = QLabel(f"👤 {user_name}  •  <span style='color: #14b8a6;'>{user_role}</span>")
        user_badge.setTextFormat(Qt.RichText)
        user_badge.setStyleSheet("""
            background-color: #1e293b;
            color: #e2e8f0;
            font-size: 12px;
            font-weight: 600;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 6px 12px;
        """)
        layout.addWidget(user_badge)

        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setFixedHeight(32)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ef4444;
                border: 1px solid #7f1d1d;
                border-radius: 6px;
                padding: 0 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
        """)
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

        # 7: Spending Heatmap
        self.heatmap_view = HeatmapView()
        self.stack.addWidget(self.heatmap_view)

        # 8: Subscriptions Tracker
        self.subscriptions_view = SubscriptionView()
        self.stack.addWidget(self.subscriptions_view)

        # 9: Budgets
        self.budgets_view = BudgetsView()
        self.stack.addWidget(self.budgets_view)

        # 10: Savings Goals
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
        self.reports_view = ReportsView()
        self.stack.addWidget(self.reports_view)

        # 17: Users & Family
        self.users_view = UsersView()
        self.stack.addWidget(self.users_view)

        # 18: Settings & Backup
        self.settings_view = SettingsView()
        self.stack.addWidget(self.settings_view)

    def open_quick_expense(self):
        """Open ultra-fast quick expense dialog."""
        from ui.expenses.quick_expense_dialog import QuickExpenseDialog
        current_page = self.stack.currentWidget()
        current_kind = getattr(current_page, "expense_kind", ExpenseKind.DAILY.value)
        dlg = QuickExpenseDialog(expense_kind=current_kind, parent=self)
        if dlg.exec():
            if hasattr(current_page, "load_expenses"):
                current_page.load_expenses()
            elif hasattr(current_page, "refresh"):
                current_page.refresh()

    def switch_page(self, idx: int):
        self.stack.setCurrentIndex(idx)
        titles = [
            "Dashboard", "Daily Expenses", "Other Expenses", "Income Management",
            "Accounts & Cards", "General Ledger", "Net Worth Tracker",
            "Spending Heatmap", "Subscription Tracker", "Budget Management", "Savings Goals",
            "Investments Portfolio", "Loans & EMIs", "Recurring Rules", "Financial Calendar",
            "Financial Planning", "Reports & Analytics", "Users & Family", "Settings & Backup"
        ]
        if idx < len(titles):
            self.page_title.setText(titles[idx])
        if hasattr(self, "navigation") and self.navigation.currentRow() != idx:
            self.navigation.setCurrentRow(idx)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            apply_app_theme(DARK)
            self.setStyleSheet(FINTECH_DARK_THEME)
            self.theme_btn.setText("🌙 Dark")
        else:
            apply_app_theme(LIGHT)
            self.setStyleSheet(LIGHT_THEME)
            self.theme_btn.setText("☀️ Light")
        if hasattr(self, "navigation"):
            self.navigation.setStyleSheet(NAVIGATION_STYLE)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.PaletteChange and hasattr(self, "navigation"):
            self.navigation.setStyleSheet(NAVIGATION_STYLE)
        super().changeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        QSettings().setValue("geometry", self.saveGeometry())
        super().closeEvent(event)

    def logout(self):
        reply = QMessageBox.question(
            self, "Logout", "Are you sure you want to sign out?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            AuthService.logout()
            self.close()
