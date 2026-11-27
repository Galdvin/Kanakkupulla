"""
Daily Spending Heatmap Calendar View:
Visually maps daily spending intensity onto an interactive month calendar grid.
Highlights high-burn days and zero-spend days with color-coded badges.
"""
from datetime import date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QComboBox, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from analytics.heatmap_service import HeatmapService
from core.financial_utils import format_inr

HEATMAP_COLORS = {
    0: "#1e293b", # Zero spending (dark background)
    1: "#065f46", # Light (< ₹1k - emerald)
    2: "#0284c7", # Medium (₹1k-₹3k - cyan/blue)
    3: "#d97706", # High (₹3k-₹8k - amber/orange)
    4: "#dc2626"  # Peak (> ₹8k - rose/red)
}

class HeatmapView(QWidget):
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
        title = QLabel("Daily Spending Heatmap")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #38bdf8;")
        sub = QLabel("Visualize daily spending intensity to immediately identify high-burn days")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.live_badge = QLabel("● Live Auto-Refresh (10s)")
        self.live_badge.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 600; padding-right: 12px;")
        header.addWidget(self.live_badge)

        # Month Selector
        self.month_combo = QComboBox()
        self.month_combo.addItems([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
        self.month_combo.setCurrentIndex(date.today().month - 1)
        self.month_combo.currentIndexChanged.connect(self.load_data)
        header.addWidget(self.month_combo)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        header.addWidget(refresh_btn)
        root.addLayout(header)

        # Periodic Auto-Refresh Timer (Every 10 seconds)
        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self.load_data)
        self.auto_timer.start(10000)

        # Legend Bar
        legend = QHBoxLayout()
        legend.addWidget(QLabel("Intensity:"))
        labels = [("Zero (₹0)", 0), ("Low (<₹1k)", 1), ("Moderate (₹1k-3k)", 2), ("High (₹3k-8k)", 3), ("Peak (>₹8k)", 4)]
        for text, lvl in labels:
            box = QLabel(f" ■ {text} ")
            box.setStyleSheet(f"color: {HEATMAP_COLORS[lvl]}; font-weight: 600; font-size: 12px;")
            legend.addWidget(box)
        legend.addStretch()
        self.total_month_lbl = QLabel("Month Total: ₹0.00")
        self.total_month_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #10b981;")
        legend.addWidget(self.total_month_lbl)
        root.addLayout(legend)

        # Calendar Grid Frame
        grid_frame = QFrame()
        grid_frame.setProperty("class", "Card")
        self.grid_layout = QGridLayout(grid_frame)
        self.grid_layout.setSpacing(8)

        # Day Headers (Mon - Sun)
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for col, d in enumerate(day_names):
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-weight: 700; color: #94a3b8; padding-bottom: 6px;")
            self.grid_layout.addWidget(lbl, 0, col)

        root.addWidget(grid_frame)
        root.addStretch()

    def refresh(self):
        self.load_data()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_data()

    def load_data(self):
        month = self.month_combo.currentIndex() + 1
        year = date.today().year
        data = HeatmapService.get_spending_heatmap(year, month)

        self.total_month_lbl.setText(f"Month Total: {format_inr(data['month_total_paise'])}")

        # Clear previous day boxes (keep header row 0)
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            row, col, _, _ = self.grid_layout.getItemPosition(i)
            if row > 0 and item.widget():
                item.widget().deleteLater()

        # Day offset calculation
        first_date = date(year, month, 1)
        start_col = first_date.weekday() # 0 = Monday

        current_row = 1
        current_col = start_col

        for d in data["days"]:
            day_num = d["day"]
            amt = d["total_paise"]
            lvl = d["intensity_level"]
            bg_color = HEATMAP_COLORS[lvl]

            box = QFrame()
            box.setFixedHeight(65)
            box.setStyleSheet(f"""
                background-color: {bg_color};
                border-radius: 8px;
                border: 1px solid #334155;
            """)
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(6, 6, 6, 6)

            day_lbl = QLabel(str(day_num))
            day_lbl.setStyleSheet("font-weight: 700; font-size: 13px; color: #f8fafc;")
            box_layout.addWidget(day_lbl)

            amt_str = f"₹{amt//100}" if amt > 0 else "-"
            amt_lbl = QLabel(amt_str)
            amt_lbl.setStyleSheet("font-size: 11px; color: #cbd5e1;")
            amt_lbl.setAlignment(Qt.AlignRight | Qt.AlignBottom)
            box_layout.addWidget(amt_lbl)

            self.grid_layout.addWidget(box, current_row, current_col)

            current_col += 1
            if current_col > 6:
                current_col = 0
                current_row += 1
