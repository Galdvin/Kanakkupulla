"""
Net Worth Analytics & Tracker View:
Displays total assets, liabilities, liquid accounts, debt-to-asset ratio, and historical breakdown.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QPushButton, QProgressBar
)
from PySide6.QtCore import Qt
from analytics.net_worth_service import NetWorthService
from core.financial_utils import format_inr
from ui.dashboard.dashboard_view import KPICard

class NetWorthView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Net Worth Tracker")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #38bdf8;")
        sub = QLabel("Total Assets minus Total Liabilities across all investments, properties, banks, and loans")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        header.addWidget(refresh_btn)
        root.addLayout(header)

        # KPI Summary Grid
        kpi_grid = QGridLayout()
        self.card_net_worth = KPICard("Current Net Worth", "₹0.00", "Total Assets - Total Liabilities", "#10b981")
        self.card_assets = KPICard("Total Assets", "₹0.00", "Bank Balances + Investments", "#38bdf8")
        self.card_liabilities = KPICard("Total Liabilities", "₹0.00", "Active Loans + Credit Cards", "#ef4444")
        self.card_ratio = KPICard("Debt-to-Asset Ratio", "0.0%", "Financial leverage health", "#f59e0b")

        kpi_grid.addWidget(self.card_net_worth, 0, 0)
        kpi_grid.addWidget(self.card_assets, 0, 1)
        kpi_grid.addWidget(self.card_liabilities, 0, 2)
        kpi_grid.addWidget(self.card_ratio, 0, 3)
        root.addLayout(kpi_grid)

        # Detailed Asset & Liability Distribution Cards
        detail_layout = QHBoxLayout()

        # Assets Card
        assets_card = QFrame()
        assets_card.setProperty("class", "Card")
        a_inner = QVBoxLayout(assets_card)
        a_title = QLabel("Asset Breakdown")
        a_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8;")
        a_inner.addWidget(a_title)
        self.assets_breakdown_layout = QVBoxLayout()
        a_inner.addLayout(self.assets_breakdown_layout)
        detail_layout.addWidget(assets_card)

        # Liabilities Card
        liab_card = QFrame()
        liab_card.setProperty("class", "Card")
        l_inner = QVBoxLayout(liab_card)
        l_title = QLabel("Liability Breakdown")
        l_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #ef4444;")
        l_inner.addWidget(l_title)
        self.liab_breakdown_layout = QVBoxLayout()
        l_inner.addLayout(self.liab_breakdown_layout)
        detail_layout.addWidget(liab_card)

        root.addLayout(detail_layout)
        root.addStretch()

    def load_data(self):
        nw = NetWorthService.calculate_current_net_worth()

        self.card_net_worth.update_value(format_inr(nw["net_worth_paise"]))
        self.card_assets.update_value(format_inr(nw["total_assets_paise"]))
        self.card_liabilities.update_value(format_inr(nw["total_liabilities_paise"]))
        self.card_ratio.update_value(f"{nw['debt_to_asset_ratio_pct']}%")

        # Assets breakdown list
        self._clear_layout(self.assets_breakdown_layout)
        self._add_row(self.assets_breakdown_layout, "Liquid Cash & Bank Accounts", nw["liquid_assets_paise"], nw["total_assets_paise"], "#38bdf8")
        self._add_row(self.assets_breakdown_layout, "Mutual Funds, Stocks & Gold", nw["investments_assets_paise"], nw["total_assets_paise"], "#10b981")

        # Liabilities breakdown list
        self._clear_layout(self.liab_breakdown_layout)
        self._add_row(self.liab_breakdown_layout, "Home & Vehicle Loans Outstanding", nw["loans_liabilities_paise"], nw["total_liabilities_paise"], "#f43f5e")
        self._add_row(self.liab_breakdown_layout, "Credit Card Outstanding", nw["credit_card_liabilities_paise"], nw["total_liabilities_paise"], "#fb923c")

    def _add_row(self, layout, title: str, amt_paise: int, total_paise: int, color: str):
        pct = int(round(amt_paise / total_paise * 100)) if total_paise > 0 else 0
        vbox = QVBoxLayout()
        header = QHBoxLayout()
        header.addWidget(QLabel(title))
        amt_lbl = QLabel(f"{format_inr(amt_paise)} ({pct}%)")
        amt_lbl.setStyleSheet("font-weight: 600; color: #f8fafc;")
        header.addStretch()
        header.addWidget(amt_lbl)
        vbox.addLayout(header)

        pbar = QProgressBar()
        pbar.setFixedHeight(8)
        pbar.setTextVisible(False)
        pbar.setValue(min(100, pct))
        pbar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}")
        vbox.addWidget(pbar)
        layout.addLayout(vbox)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
