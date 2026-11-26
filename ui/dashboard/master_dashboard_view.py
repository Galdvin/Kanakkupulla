"""
Master Dashboard View (Version 2.0 - Family Finance Platform)
Rich Graphical Fintech Dashboard:
1. Header with View Mode (Family Consolidated vs Individual Member) & Date Range selector
2. 8 Enhanced Fintech KPI Cards with icon badges & accent gradients
3. Cash Flow & Net Savings Trend Chart (Last 6 Months grouped bar chart)
4. Category Spending Donut Chart with center metrics & interactive legend
5. Financial Health & Savings Rate Radial Arc Gauge
6. Family Member Spending Attribution with segmented proportion bar & cards
7. Recent Financial Activity Stream with transaction category & account chips
"""
from datetime import date, timedelta
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QComboBox, QPushButton, QScrollArea, QProgressBar,
    QSizePolicy
)
from PySide6.QtCore import Qt
from analytics.expense_analysis import AnalyticsService
from core.family_service import FamilyService
from core.financial_utils import format_inr, format_date
from ui.dashboard.dashboard_charts import (
    ModernDonutChart, CashFlowTrendBarChart, SavingsHealthGauge, 
    MemberSpendingSegmentedBar, CHART_PALETTE
)


class FintechKPICard(QFrame):
    """Modern Fintech Metric Card with top accent indicator, icon badge, and crisp typography."""
    def __init__(self, title: str, initial_value: str = "₹0.00", subtitle: str = "", accent_color: str = "#14b8a6", icon: str = "📊"):
        super().__init__()
        self.accent_color = accent_color
        self.setStyleSheet(f"""
            FintechKPICard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #111a2e, stop:1 #0b1120);
                border: 1px solid #1e293b;
                border-top: 3px solid {accent_color};
                border-radius: 10px;
            }}
            FintechKPICard:hover {{
                border-color: #334155;
                border-top: 3px solid {accent_color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        # Top row: Title + Icon
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        
        t_lbl = QLabel(title.upper())
        t_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.5px;")
        top_row.addWidget(t_lbl)
        top_row.addStretch()

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 14px; background: rgba(30, 41, 59, 0.6); border-radius: 6px; padding: 2px 6px;")
        top_row.addWidget(icon_lbl)
        layout.addLayout(top_row)

        # Value
        self.val_lbl = QLabel(initial_value)
        self.val_lbl.setStyleSheet(f"font-size: 21px; font-weight: 800; color: {accent_color}; margin-top: 2px;")
        layout.addWidget(self.val_lbl)

        # Subtitle
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.sub_lbl)

    def update_value(self, value_text: str, subtitle_text: str = ""):
        self.val_lbl.setText(value_text)
        if subtitle_text:
            self.sub_lbl.setText(subtitle_text)


class MasterFamilyDashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(14)

        # ----------------- Top Header Bar -----------------
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

        # Viewing Mode Selector
        header.addWidget(QLabel("View Mode:"))
        self.member_combo = QComboBox()
        self.member_combo.setFixedHeight(34)
        self.member_combo.addItem("👨‍👩‍👧‍👦 Family Overview (Consolidated)", None)
        for m in FamilyService.get_all_members():
            self.member_combo.addItem(f"👤 {m.name} ({m.relation_type})", m.id)
        self.member_combo.currentIndexChanged.connect(self.load_data)
        header.addWidget(self.member_combo)

        # Period Filter
        header.addWidget(QLabel("Period:"))
        self.period_combo = QComboBox()
        self.period_combo.setFixedHeight(34)
        self.period_combo.addItems([
            "This Month", "Last Month", "Last 3 Months", "Last 6 Months", "This Year", "All Time"
        ])
        self.period_combo.currentIndexChanged.connect(self.load_data)
        header.addWidget(self.period_combo)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedHeight(34)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #1e293b;
                color: #f8fafc;
                font-weight: 600;
                padding: 6px 14px;
                border: 1px solid #334155;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #334155;
            }
        """)
        refresh_btn.clicked.connect(self.load_data)
        header.addWidget(refresh_btn)
        root.addLayout(header)

        # ----------------- Scrollable Container -----------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setContentsMargins(0, 0, 8, 16)
        scroll_layout.setSpacing(18)

        # ----------------- 1. 8 Core KPI Cards -----------------
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(12)

        self.card_income = FintechKPICard("Total Family Income", "₹0.00", "Posted income", "#10b981", "💰")
        self.card_expense = FintechKPICard("Total Family Expenses", "₹0.00", "Net of refunds", "#ef4444", "💸")
        self.card_savings = FintechKPICard("Total Family Savings", "₹0.00", "Income - Expenses", "#14b8a6", "🛡")
        self.card_balance = FintechKPICard("Available Bank Balance", "₹0.00", "All liquid accounts", "#38bdf8", "🏦")

        self.card_budget = FintechKPICard("Monthly Budget Remaining", "₹0.00", "Allocated plan", "#a855f7", "🎯")
        self.card_investments = FintechKPICard("Total Investments", "₹0.00", "Current valuation", "#06b6d4", "📈")
        self.card_liabilities = FintechKPICard("Total Liabilities", "₹0.00", "Loans & Cards", "#f43f5e", "💳")
        self.card_net_worth = FintechKPICard("Family Net Worth", "₹0.00", "Assets - Liabilities", "#f59e0b", "💎")

        kpi_grid.addWidget(self.card_income, 0, 0)
        kpi_grid.addWidget(self.card_expense, 0, 1)
        kpi_grid.addWidget(self.card_savings, 0, 2)
        kpi_grid.addWidget(self.card_balance, 0, 3)

        kpi_grid.addWidget(self.card_budget, 1, 0)
        kpi_grid.addWidget(self.card_investments, 1, 1)
        kpi_grid.addWidget(self.card_liabilities, 1, 2)
        kpi_grid.addWidget(self.card_net_worth, 1, 3)

        scroll_layout.addLayout(kpi_grid)

        # ----------------- 2. Charts Row: Trend Chart (Left) + Donut (Right) -----------------
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        # Cash Flow Trend Card
        trend_card = QFrame()
        trend_card.setProperty("class", "Card")
        trend_card.setStyleSheet("""
            QFrame {
                background: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)
        trend_layout = QVBoxLayout(trend_card)
        trend_layout.setContentsMargins(18, 16, 18, 16)
        trend_layout.setSpacing(10)

        trend_header = QHBoxLayout()
        t_box = QVBoxLayout()
        t_title = QLabel("Cash Flow & Net Savings Trend")
        t_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        t_sub = QLabel("Month-by-month trajectory comparing posted income vs living expenses")
        t_sub.setStyleSheet("font-size: 11px; color: #64748b;")
        t_box.addWidget(t_title)
        t_box.addWidget(t_sub)
        trend_header.addLayout(t_box)
        trend_header.addStretch()
        trend_layout.addLayout(trend_header)

        self.trend_chart = CashFlowTrendBarChart()
        trend_layout.addWidget(self.trend_chart)
        charts_row.addWidget(trend_card, stretch=6)

        # Category Donut Card
        donut_card = QFrame()
        donut_card.setProperty("class", "Card")
        donut_card.setStyleSheet("""
            QFrame {
                background: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)
        donut_layout = QVBoxLayout(donut_card)
        donut_layout.setContentsMargins(18, 16, 18, 16)
        donut_layout.setSpacing(10)

        d_box = QVBoxLayout()
        d_title = QLabel("Category Spending Breakdown")
        d_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        d_sub = QLabel("Proportional distribution across all spending categories")
        d_sub.setStyleSheet("font-size: 11px; color: #64748b;")
        d_box.addWidget(d_title)
        d_box.addWidget(d_sub)
        donut_layout.addLayout(d_box)

        donut_content = QHBoxLayout()
        donut_content.setSpacing(14)

        self.donut_chart = ModernDonutChart()
        donut_content.addWidget(self.donut_chart, stretch=5)

        self.cat_legend_layout = QVBoxLayout()
        self.cat_legend_layout.setSpacing(8)
        self.cat_legend_layout.setAlignment(Qt.AlignVCenter)
        donut_content.addLayout(self.cat_legend_layout, stretch=6)

        donut_layout.addLayout(donut_content)
        charts_row.addWidget(donut_card, stretch=5)

        scroll_layout.addLayout(charts_row)

        # ----------------- 3. Health & Attribution Row -----------------
        health_row = QHBoxLayout()
        health_row.setSpacing(16)

        # Savings Gauge Card
        gauge_card = QFrame()
        gauge_card.setStyleSheet("""
            QFrame {
                background: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)
        gauge_layout = QVBoxLayout(gauge_card)
        gauge_layout.setContentsMargins(18, 16, 18, 16)
        gauge_layout.setSpacing(8)

        g_title = QLabel("Financial Health & Savings Pace")
        g_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        g_sub = QLabel("Ratio of saved revenue vs total incoming family cash flow")
        g_sub.setStyleSheet("font-size: 11px; color: #64748b;")
        gauge_layout.addWidget(g_title)
        gauge_layout.addWidget(g_sub)

        gauge_inner = QHBoxLayout()
        self.savings_gauge = SavingsHealthGauge()
        gauge_inner.addWidget(self.savings_gauge, stretch=4)

        # Budget Burn Sub-Panel
        budget_box = QVBoxLayout()
        budget_box.setSpacing(8)
        budget_box.setAlignment(Qt.AlignVCenter)

        bb_title = QLabel("Monthly Budget Burn")
        bb_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #94a3b8;")
        budget_box.addWidget(bb_title)

        self.budget_burn_bar = QProgressBar()
        self.budget_burn_bar.setFixedHeight(10)
        self.budget_burn_bar.setTextVisible(False)
        self.budget_burn_bar.setStyleSheet("""
            QProgressBar {
                background: #1e293b;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0d9488, stop:1 #14b8a6);
                border-radius: 5px;
            }
        """)
        budget_box.addWidget(self.budget_burn_bar)

        self.budget_burn_lbl = QLabel("0.0% Utilized (₹0.00 Remaining)")
        self.budget_burn_lbl.setStyleSheet("font-size: 11px; color: #cbd5e1; font-weight: 600;")
        budget_box.addWidget(self.budget_burn_lbl)

        gauge_inner.addLayout(budget_box, stretch=5)
        gauge_layout.addLayout(gauge_inner)
        health_row.addWidget(gauge_card, stretch=5)

        # Member Spending Attribution Card
        member_card = QFrame()
        member_card.setStyleSheet("""
            QFrame {
                background: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)
        member_layout = QVBoxLayout(member_card)
        member_layout.setContentsMargins(18, 16, 18, 16)
        member_layout.setSpacing(12)

        m_title = QLabel("Member Spending Attribution")
        m_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        m_sub = QLabel("Proportional family member expenditure share in selected period")
        m_sub.setStyleSheet("font-size: 11px; color: #64748b;")
        member_layout.addWidget(m_title)
        member_layout.addWidget(m_sub)

        self.member_segmented_bar = MemberSpendingSegmentedBar()
        member_layout.addWidget(self.member_segmented_bar)

        self.member_chips_layout = QVBoxLayout()
        self.member_chips_layout.setSpacing(6)
        member_layout.addLayout(self.member_chips_layout)
        member_layout.addStretch()

        health_row.addWidget(member_card, stretch=6)

        scroll_layout.addLayout(health_row)

        # ----------------- 4. Recent Financial Activity Stream -----------------
        activity_card = QFrame()
        activity_card.setStyleSheet("""
            QFrame {
                background: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)
        activity_layout = QVBoxLayout(activity_card)
        activity_layout.setContentsMargins(18, 16, 18, 16)
        activity_layout.setSpacing(10)

        act_title = QLabel("Recent Financial Activity")
        act_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        act_sub = QLabel("Live transaction flow across personal and family accounts")
        act_sub.setStyleSheet("font-size: 11px; color: #64748b;")
        activity_layout.addWidget(act_title)
        activity_layout.addWidget(act_sub)

        self.activity_list_layout = QVBoxLayout()
        self.activity_list_layout.setSpacing(8)
        activity_layout.addLayout(self.activity_list_layout)

        scroll_layout.addWidget(activity_card)

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
        self.card_savings.update_value(
            format_inr(metrics["total_savings_paise"]),
            f"Savings Rate: {metrics['savings_rate_pct']}%"
        )
        self.card_balance.update_value(format_inr(metrics["liquid_balance_paise"]))

        self.card_budget.update_value(
            format_inr(metrics["budget_remaining_paise"]),
            f"{metrics['budget_utilization_pct']}% Utilized"
        )
        self.card_investments.update_value(format_inr(metrics["total_investments_paise"]))
        self.card_liabilities.update_value(format_inr(metrics["total_liabilities_paise"]))
        self.card_net_worth.update_value(format_inr(metrics["family_net_worth_paise"]))

        # 1. Update Trend Bar Chart
        trend_data = AnalyticsService.get_cash_flow_trend(months=6, filter_member_id=selected_member_id)
        self.trend_chart.set_data(trend_data)

        # 2. Update Category Donut Chart & Legend
        cats = metrics["category_distribution"]
        total_exp = metrics["total_expense_paise"]
        self.donut_chart.set_data(cats, total_exp, "Total Spent")

        self._clear_layout(self.cat_legend_layout)
        if not cats:
            lbl = QLabel("No expenses recorded in this period.")
            lbl.setStyleSheet("color: #64748b; font-style: italic; font-size: 12px;")
            self.cat_legend_layout.addWidget(lbl)
        else:
            for idx, c in enumerate(cats[:5]):  # Top 5 categories
                color = CHART_PALETTE[idx % len(CHART_PALETTE)]
                pct = (c["amount_paise"] / total_exp * 100.0) if total_exp > 0 else 0.0

                row = QHBoxLayout()
                row.setSpacing(8)

                # Colored dot
                dot = QLabel("●")
                dot.setStyleSheet(f"color: {color}; font-size: 13px;")
                row.addWidget(dot)

                # Category name
                name_lbl = QLabel(c["name"])
                name_lbl.setStyleSheet("color: #f1f5f9; font-size: 12px; font-weight: 500;")
                row.addWidget(name_lbl)
                row.addStretch()

                # Amount
                amt_lbl = QLabel(format_inr(c["amount_paise"]))
                amt_lbl.setStyleSheet("color: #f8fafc; font-size: 12px; font-weight: 600;")
                row.addWidget(amt_lbl)

                # Percentage badge
                badge = QLabel(f"{pct:.1f}%")
                badge.setStyleSheet(f"""
                    background: {color}22;
                    color: {color};
                    font-size: 10px;
                    font-weight: 700;
                    padding: 2px 6px;
                    border-radius: 4px;
                """)
                row.addWidget(badge)

                self.cat_legend_layout.addLayout(row)

        # 3. Update Savings Health Gauge & Budget Burn
        self.savings_gauge.set_rate(metrics["savings_rate_pct"])
        self.budget_burn_bar.setValue(int(min(100, metrics["budget_utilization_pct"])))
        self.budget_burn_lbl.setText(
            f"{metrics['budget_utilization_pct']}% Utilized ({format_inr(metrics['budget_remaining_paise'])} Remaining)"
        )

        # 4. Update Member Spending Attribution
        payers = metrics["user_distribution"]
        self.member_segmented_bar.set_data(payers, total_exp)

        self._clear_layout(self.member_chips_layout)
        if not payers:
            lbl = QLabel("No member expense recorded in this period.")
            lbl.setStyleSheet("color: #64748b; font-style: italic; font-size: 12px;")
            self.member_chips_layout.addWidget(lbl)
        else:
            for idx, p in enumerate(payers):
                color = CHART_PALETTE[idx % len(CHART_PALETTE)]
                pct = (p["amount_paise"] / total_exp * 100.0) if total_exp > 0 else 0.0

                row = QHBoxLayout()
                row.setSpacing(8)

                avatar = QLabel("👤")
                avatar.setStyleSheet("font-size: 12px;")
                row.addWidget(avatar)

                pname = QLabel(p["user"])
                pname.setStyleSheet("color: #f1f5f9; font-size: 12px; font-weight: 500;")
                row.addWidget(pname)
                row.addStretch()

                amt = QLabel(format_inr(p["amount_paise"]))
                amt.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 600;")
                row.addWidget(amt)

                pct_badge = QLabel(f"{pct:.1f}%")
                pct_badge.setStyleSheet(f"""
                    background: {color}22;
                    color: {color};
                    font-size: 10px;
                    font-weight: 700;
                    padding: 2px 6px;
                    border-radius: 4px;
                """)
                row.addWidget(pct_badge)

                self.member_chips_layout.addLayout(row)

        # 5. Update Recent Financial Activity Feed
        recent_activity = AnalyticsService.get_recent_activity(limit=5, filter_member_id=selected_member_id)
        self._clear_layout(self.activity_list_layout)

        if not recent_activity:
            lbl = QLabel("No recent transactions found.")
            lbl.setStyleSheet("color: #64748b; font-style: italic; font-size: 12px;")
            self.activity_list_layout.addWidget(lbl)
        else:
            for act in recent_activity:
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background: #111a2e;
                        border: 1px solid #1e293b;
                        border-radius: 8px;
                        padding: 6px;
                    }
                    QFrame:hover {
                        background: #162238;
                        border-color: #334155;
                    }
                """)
                r_layout = QHBoxLayout(card)
                r_layout.setContentsMargins(12, 8, 12, 8)
                r_layout.setSpacing(12)

                # Type Icon badge
                is_income = act["type"].lower() == "income"
                is_transfer = act["type"].lower() == "transfer"
                icon_text = "↑" if is_income else ("⇄" if is_transfer else "↓")
                icon_color = "#10b981" if is_income else ("#38bdf8" if is_transfer else "#ef4444")
                icon_bg = "#10b98122" if is_income else ("#38bdf822" if is_transfer else "#ef444422")

                badge = QLabel(icon_text)
                badge.setFixedSize(28, 28)
                badge.setAlignment(Qt.AlignCenter)
                badge.setStyleSheet(f"""
                    background: {icon_bg};
                    color: {icon_color};
                    font-weight: 800;
                    font-size: 14px;
                    border-radius: 6px;
                """)
                r_layout.addWidget(badge)

                # Title & Category
                t_box = QVBoxLayout()
                t_box.setSpacing(2)
                t_lbl = QLabel(act["title"])
                t_lbl.setStyleSheet("color: #f8fafc; font-size: 13px; font-weight: 600;")
                cat_lbl = QLabel(f"📂 {act['category']} • 👤 {act['member']} • 🏦 {act['account']}")
                cat_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
                t_box.addWidget(t_lbl)
                t_box.addWidget(cat_lbl)
                r_layout.addLayout(t_box)
                r_layout.addStretch()

                # Date
                d_lbl = QLabel(format_date(act["date"]))
                d_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
                r_layout.addWidget(d_lbl)

                # Amount
                sign = "+" if is_income else ("" if is_transfer else "-")
                amt_str = f"{sign}{format_inr(act['amount_paise'])}"
                amt_lbl = QLabel(amt_str)
                amt_lbl.setStyleSheet(f"color: {icon_color}; font-size: 14px; font-weight: 700;")
                r_layout.addWidget(amt_lbl)

                self.activity_list_layout.addWidget(card)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
