"""
Financial Calendar View:
Interactive month-by-month calendar displaying daily spending aggregates,
income credits, scheduled bill due dates, and loan EMI events.
"""
from typing import Optional
from datetime import date
import calendar
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QScrollArea, QListWidget, QListWidgetItem,
    QSplitter
)
from PySide6.QtCore import Qt
from core.calendar_service import CalendarService

class DayCellWidget(QFrame):
    def __init__(self, day_info: Optional[dict], is_current_month: bool, on_click_callback=None, parent=None):
        super().__init__(parent)
        self.day_info = day_info
        self.on_click_callback = on_click_callback

        self.setMinimumSize(90, 85)
        self.setCursor(Qt.PointingHandCursor)

        border_col = "#334155" if is_current_month else "#1e293b"
        bg_col = "#1e293b" if is_current_month else "#0b1329"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 6px;
                padding: 4px;
            }}
            QFrame:hover {{
                border: 1px solid #0ea5e9;
                background-color: #27354f;
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(2)

        if not day_info:
            return

        # Day Number header
        top_row = QHBoxLayout()
        d_lbl = QLabel(str(day_info["day"]))
        is_today = day_info["date"] == date.today()
        d_lbl.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 13px;" if is_today else "color: #94a3b8; font-weight: 600; font-size: 12px;")
        top_row.addWidget(d_lbl)
        top_row.addStretch()

        # Scheduled badge count
        sched_count = len(day_info.get("scheduled_events", []))
        if sched_count > 0:
            s_badge = QLabel(f"⚡ {sched_count}")
            s_badge.setStyleSheet("background-color: #78350f; color: #fbbf24; font-size: 9px; font-weight: 700; padding: 1px 4px; border-radius: 3px;")
            top_row.addWidget(s_badge)

        lay.addLayout(top_row)

        # Actual Expense pill
        exp_paise = day_info.get("actual_expense_paise", 0)
        if exp_paise > 0:
            exp_pill = QLabel(f"-₹{exp_paise / 100:,.0f}")
            exp_pill.setStyleSheet("color: #f43f5e; font-size: 11px; font-weight: 600;")
            lay.addWidget(exp_pill)

        # Actual Income pill
        inc_paise = day_info.get("actual_income_paise", 0)
        if inc_paise > 0:
            inc_pill = QLabel(f"+₹{inc_paise / 100:,.0f}")
            inc_pill.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 600;")
            lay.addWidget(inc_pill)

        lay.addStretch()

    def mousePressEvent(self, event):
        if self.day_info and self.on_click_callback:
            self.on_click_callback(self.day_info)
        super().mousePressEvent(event)


class CalendarView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        today = date.today()
        self.current_year = today.year
        self.current_month = today.month

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(14)

        # Header bar (Title + Month Controls)
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Financial Calendar")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #f8fafc;")
        sub_lbl = QLabel("Daily spending intensity, upcoming bill deadlines, and EMI schedules.")
        sub_lbl.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Navigation Controls
        prev_btn = QPushButton("◀ Prev")
        prev_btn.setStyleSheet("background-color: #1e293b; color: #f8fafc; padding: 6px 12px; border-radius: 6px; border: 1px solid #334155;")
        prev_btn.clicked.connect(self.prev_month)
        header_layout.addWidget(prev_btn)

        self.month_year_lbl = QLabel()
        self.month_year_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8; min-width: 140px;")
        self.month_year_lbl.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.month_year_lbl)

        next_btn = QPushButton("Next ▶")
        next_btn.setStyleSheet("background-color: #1e293b; color: #f8fafc; padding: 6px 12px; border-radius: 6px; border: 1px solid #334155;")
        next_btn.clicked.connect(self.next_month)
        header_layout.addWidget(next_btn)

        today_btn = QPushButton("Today")
        today_btn.setStyleSheet("background-color: #0284c7; color: white; padding: 6px 14px; border-radius: 6px; font-weight: 600;")
        today_btn.clicked.connect(self.go_today)
        header_layout.addWidget(today_btn)

        self.layout.addLayout(header_layout)

        # Monthly Stats Bar
        self.stats_bar = QFrame()
        self.stats_bar.setStyleSheet("background-color: #1e293b; border-radius: 8px; padding: 10px 16px; border: 1px solid #334155;")
        self.stats_layout = QHBoxLayout(self.stats_bar)
        self.stats_layout.setContentsMargins(8, 4, 8, 4)
        self.layout.addWidget(self.stats_bar)

        # Main splitter (Calendar Grid on Left, Day Details on Right)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #334155; width: 2px; }")

        # Calendar Container
        calendar_widget = QWidget()
        self.cal_layout = QVBoxLayout(calendar_widget)
        self.cal_layout.setContentsMargins(0, 0, 10, 0)
        self.cal_layout.setSpacing(8)

        # Day Names Header (Mon - Sun)
        days_header = QHBoxLayout()
        for d_name in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            lbl = QLabel(d_name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #64748b; font-weight: 700; font-size: 12px;")
            days_header.addWidget(lbl)
        self.cal_layout.addLayout(days_header)

        # 7-Column Grid
        self.grid = QGridLayout()
        self.grid.setSpacing(6)
        self.cal_layout.addLayout(self.grid)
        splitter.addWidget(calendar_widget)

        # Day Details Side Panel
        details_widget = QFrame()
        details_widget.setStyleSheet("background-color: #1e293b; border-radius: 8px; border: 1px solid #334155; padding: 14px;")
        self.details_layout = QVBoxLayout(details_widget)
        self.details_layout.setSpacing(10)

        self.day_title_lbl = QLabel("Select a date to view activity")
        self.day_title_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8;")
        self.details_layout.addWidget(self.day_title_lbl)

        self.events_list = QListWidget()
        self.events_list.setStyleSheet("""
            QListWidget {
                background-color: #0f172a; border: 1px solid #334155;
                border-radius: 6px; padding: 6px; color: #f8fafc;
            }
            QListWidget::item {
                padding: 8px; border-bottom: 1px solid #1e293b;
            }
        """)
        self.details_layout.addWidget(self.events_list)
        splitter.addWidget(details_widget)

        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        self.layout.addWidget(splitter)

        self.load_month_data()

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.load_month_data()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.load_month_data()

    def go_today(self):
        today = date.today()
        self.current_year = today.year
        self.current_month = today.month
        self.load_month_data()

    def load_month_data(self):
        # Update Month Label
        self.month_year_lbl.setText(f"{calendar.month_name[self.current_month]} {self.current_year}")

        data = CalendarService.get_month_calendar_data(self.current_year, self.current_month)

        # Update Stats Bar
        while self.stats_layout.count():
            item = self.stats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        net = data["net_cashflow_paise"]
        net_col = "#10b981" if net >= 0 else "#f43f5e"
        net_prefix = "+" if net >= 0 else ""

        self._add_stat_pill("Spent This Month", f"₹{data['total_actual_expense_paise'] / 100:,.2f}", "#f43f5e")
        self._add_stat_pill("Income Received", f"₹{data['total_actual_income_paise'] / 100:,.2f}", "#10b981")
        self._add_stat_pill("Net Cashflow", f"{net_prefix}₹{net / 100:,.2f}", net_col)
        self._add_stat_pill("Scheduled Bills & EMIs", f"₹{data['total_scheduled_expense_paise'] / 100:,.2f}", "#fbbf24")
        self.stats_layout.addStretch()

        # Clear Grid
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Fill Grid
        first_col = data["first_weekday"] # 0 = Mon, 6 = Sun
        num_days = data["num_days"]
        daily_data = data["daily_data"]

        # Blank spaces before first day
        row = 0
        col = 0
        for _ in range(first_col):
            empty_cell = DayCellWidget(None, is_current_month=False)
            self.grid.addWidget(empty_cell, row, col)
            col += 1

        for day in range(1, num_days + 1):
            day_info = daily_data[day]
            cell = DayCellWidget(day_info, is_current_month=True, on_click_callback=self.on_day_selected)
            self.grid.addWidget(cell, row, col)
            col += 1
            if col == 7:
                col = 0
                row += 1

        # Select today if in current month
        today = date.today()
        if today.year == self.current_year and today.month == self.current_month:
            self.on_day_selected(daily_data[today.day])
        else:
            self.on_day_selected(daily_data[1])

    def _add_stat_pill(self, label: str, value: str, val_color: str):
        box = QHBoxLayout()
        box.setSpacing(6)
        l = QLabel(f"{label}:")
        l.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        v = QLabel(value)
        v.setStyleSheet(f"color: {val_color}; font-size: 13px; font-weight: 700;")
        box.addWidget(l)
        box.addWidget(v)
        self.stats_layout.addLayout(box)
        self.stats_layout.addSpacing(18)

    def on_day_selected(self, day_info: dict):
        d = day_info["date"]
        self.day_title_lbl.setText(f"Activity for {d.strftime('%A, %d %B %Y')}")
        self.events_list.clear()

        # Scheduled Events
        sched = day_info.get("scheduled_events", [])
        if sched:
            s_header = QListWidgetItem("⚡ SCHEDULED BILLS & LIABILITIES:")
            s_header.setFlags(s_header.flags() ^ Qt.ItemIsSelectable)
            s_header.setForeground(Qt.yellow)
            self.events_list.addItem(s_header)
            for s in sched:
                item_str = f"  • {s['title']} — ₹{s['amount_paise'] / 100:,.2f} ({s['kind']})"
                it = QListWidgetItem(item_str)
                it.setForeground(Qt.white)
                self.events_list.addItem(it)

        # Actual Transactions
        txns = day_info.get("transactions", [])
        if txns:
            t_header = QListWidgetItem("\n📝 RECORDED TRANSACTIONS:")
            t_header.setFlags(t_header.flags() ^ Qt.ItemIsSelectable)
            t_header.setForeground(Qt.cyan)
            self.events_list.addItem(t_header)
            for t in txns:
                sign = "-" if t["type"] == "Expense" else "+"
                col = "#f43f5e" if t["type"] == "Expense" else "#10b981"
                item_str = f"  • {t['title']} ({t['category']}) — {sign}₹{t['amount_paise'] / 100:,.2f} [Paid by {t['paid_by']}]"
                it = QListWidgetItem(item_str)
                it.setForeground(Qt.white)
                self.events_list.addItem(it)

        if not sched and not txns:
            empty_it = QListWidgetItem("No transactions or scheduled commitments on this date.")
            empty_it.setForeground(Qt.gray)
            self.events_list.addItem(empty_it)
