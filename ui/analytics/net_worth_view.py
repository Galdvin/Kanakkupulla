"""
Modern Glassmorphic Net Worth Analytics & Solvency Tracker View:
- High-Performance QWebEngineView hosting Tailwind CSS + Glassmorphism + Recharts-style SVG
- 4 Glowing Gradient KPI Cards (Net Worth, Total Assets, Total Liabilities, Debt-to-Asset Ratio)
- Interactive Net Worth Growth & Trajectory SVG Pace Curve with Tooltips
- Proportional Asset & Liability Donut Rings with Glowing Visualizers
- Capital Solvency Score & Emergency Cash Runway Gauge
- Itemized Accounts & Portfolio Holdings Glass Tables
- 100% Offline with bidirectional QWebChannel bridge
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QUrl, QObject, Slot
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel

from analytics.net_worth_service import NetWorthService


class NetWorthBridge(QObject):
    """Bridge for receiving JavaScript signals from web_net_worth.html."""
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view

    @Slot()
    def onRefresh(self):
        self.parent_view.load_data()


class NetWorthView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.web_view = QWebEngineView()
        
        # Configure local offline security settings
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)

        # Set up QWebChannel
        self.channel = QWebChannel(self)
        self.bridge = NetWorthBridge(self)
        self.channel.registerObject("pyBridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # Load local HTML file
        html_path = Path(__file__).parent / "web_net_worth.html"
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
            self.load_data()

    def refresh(self):
        self.load_data()

    def load_data(self):
        data = NetWorthService.get_detailed_net_worth()
        json_str = json.dumps(data)
        js_code = f"if (window.updateNetWorthData) {{ window.updateNetWorthData({json_str}); }}"
        self.web_view.page().runJavaScript(js_code)
