"""
WebEngine-Powered Glassmorphism Financial Intelligence Dashboard
Hosts Tailwind CSS + Glassmorphism + Recharts-style interactive SVG + Lucide Icons
Communicates via bidirectional QWebChannel & runJavaScript bridge.
"""
import os
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QUrl, QObject, Slot
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel

from analytics.expense_analysis import AnalyticsService
from analytics.forecasting import ForecastingEngine
from core.family_service import FamilyService
from core.financial_utils import format_inr, format_date


class DashboardBridge(QObject):
    """Bridge for receiving JavaScript calls from the WebEngine dashboard."""
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view

    @Slot(str, str)
    def onFilterChange(self, member_id_str: str, period_str: str):
        member_id = int(member_id_str) if member_id_str and member_id_str.isdigit() else None
        self.parent_view.apply_filter(member_id, period_str)


class WebDashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_member_id: Optional[int] = None
        self.current_period: str = "This Month"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.web_view = QWebEngineView()
        
        # WebEngine settings for smooth local offline experience
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)

        # Set up QWebChannel
        self.channel = QWebChannel(self)
        self.bridge = DashboardBridge(self)
        self.channel.registerObject("pyBridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # Inject qwebchannel.js initialization
        qwebchannel_js_path = ":/qtwebchannel/qwebchannel.js"

        # Load local HTML file
        html_path = Path(__file__).parent / "web_dashboard.html"
        self.web_view.setUrl(QUrl.fromLocalFile(str(html_path.resolve())))
        self.web_view.loadFinished.connect(self.on_load_finished)

        layout.addWidget(self.web_view)

    def on_load_finished(self, ok: bool):
        if ok:
            # Inject QWebChannel bridge initialization script into page
            setup_script = """
            if (typeof QWebChannel !== 'undefined') {
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    window.pyBridge = channel.objects.pyBridge;
                });
            }
            """
            self.web_view.page().runJavaScript(setup_script)
            self.refresh_data()

    def get_date_range(self) -> tuple[date, date]:
        period = self.current_period
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

    def apply_filter(self, member_id: Optional[int], period: str):
        self.current_member_id = member_id
        self.current_period = period or "This Month"
        self.refresh_data()

    def refresh(self):
        self.refresh_data()

    def refresh_data(self):
        start_date, end_date = self.get_date_range()
        selected_member_id = self.current_member_id

        # 1. Dashboard Metrics
        metrics = AnalyticsService.get_dashboard_metrics(
            start_date=start_date,
            end_date=end_date,
            filter_member_id=selected_member_id
        )

        # 2. Cash Flow Trend (Last 6 Months)
        cash_flow_trend = AnalyticsService.get_cash_flow_trend(
            months=6,
            filter_member_id=selected_member_id
        )

        # 3. 12-Month Cashflow & Demand Forecasting
        try:
            forecast_data = ForecastingEngine.project_12_month_cashflow()
            forecast_trend = []
            for item in forecast_data.get("projections", []):
                forecast_trend.append({
                    "month_short": item.get("month", "")[:3],
                    "month_label": item.get("month", ""),
                    "income_paise": item.get("income_paise", 0),
                    "expense_paise": item.get("expenses_paise", 0),
                    "savings_paise": item.get("net_savings_paise", 0),
                })
        except Exception:
            forecast_trend = []

        # 4. Recent Activity
        recent_activity_raw = AnalyticsService.get_recent_activity(
            limit=5,
            filter_member_id=selected_member_id
        )
        recent_activity = []
        for r in recent_activity_raw:
            recent_activity.append({
                "id": r["id"],
                "date": format_date(r["date"]),
                "title": r["title"],
                "type": r["type"],
                "amount_paise": r["amount_paise"],
                "category": r["category"],
                "member": r["member"],
                "account": r["account"]
            })

        # 5. Members List for Selector
        members = [
            {"id": m.id, "name": m.name, "relation_type": m.relation_type or "Member"}
            for m in FamilyService.get_all_members()
        ]

        payload = {
            "members": members,
            "total_income_paise": metrics["total_income_paise"],
            "total_expense_paise": metrics["total_expense_paise"],
            "total_savings_paise": metrics["total_savings_paise"],
            "savings_rate_pct": metrics["savings_rate_pct"],
            "liquid_balance_paise": metrics["liquid_balance_paise"],
            "budget_remaining_paise": metrics["budget_remaining_paise"],
            "budget_utilization_pct": metrics["budget_utilization_pct"],
            "total_investments_paise": metrics["total_investments_paise"],
            "total_liabilities_paise": metrics["total_liabilities_paise"],
            "family_net_worth_paise": metrics["family_net_worth_paise"],
            "category_distribution": metrics["category_distribution"],
            "user_distribution": metrics["user_distribution"],
            "cash_flow_trend": cash_flow_trend,
            "forecast_trend": forecast_trend,
            "recent_activity": recent_activity
        }

        json_str = json.dumps(payload)
        js_code = f"window.updateDashboardData({json_str});"
        self.web_view.page().runJavaScript(js_code)
