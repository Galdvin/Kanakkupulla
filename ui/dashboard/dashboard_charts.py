"""
Modern Fintech Graphical Dashboard Charts
Custom QPainter-based high-performance offline charts:
- ModernDonutChart: Vector donut chart with center metrics & interactive legends
- CashFlowTrendBarChart: Grouped rounded-bar chart for Income vs Expense trend
- SavingsHealthGauge: Radial arc gauge for savings rate & budget health
- MemberAttributionSegmentedBar: Segmented multi-color proportion bar
- RecentActivityStream: Modern fintech transaction feed
"""
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QRectF, QPointF, QSize
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QBrush, QPen, QFont, QLinearGradient, QFontMetrics
)
from core.financial_utils import format_inr, format_date

CHART_PALETTE = [
    "#0d9488",  # Teal / Primary
    "#38bdf8",  # Sky Blue
    "#8b5cf6",  # Violet
    "#f59e0b",  # Amber
    "#ec4899",  # Pink
    "#06b6d4",  # Cyan
    "#10b981",  # Emerald
    "#f97316",  # Orange
    "#6366f1",  # Indigo
    "#f43f5e",  # Rose
]


class ModernDonutChart(QWidget):
    """Vector Donut Chart with center value display and category slices."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.slices: List[Dict[str, Any]] = []
        self.total_amount_paise: int = 0
        self.center_title: str = "Total Spent"

    def set_data(self, categories: List[Dict[str, Any]], total_paise: int, center_title: str = "Total Spent"):
        self.slices = []
        self.total_amount_paise = total_paise
        self.center_title = center_title

        if total_paise > 0:
            for idx, c in enumerate(categories):
                color = CHART_PALETTE[idx % len(CHART_PALETTE)]
                pct = (c["amount_paise"] / total_paise) * 100
                self.slices.append({
                    "name": c["name"],
                    "amount_paise": c["amount_paise"],
                    "percentage": pct,
                    "color": color
                })
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        outer_radius = min(w, h) / 2.0 - 14.0
        inner_radius = outer_radius * 0.65

        if outer_radius <= 20:
            return

        outer_rect = QRectF(cx - outer_radius, cy - outer_radius, outer_radius * 2, outer_radius * 2)
        inner_rect = QRectF(cx - inner_radius, cy - inner_radius, inner_radius * 2, inner_radius * 2)

        # Empty State
        if not self.slices or self.total_amount_paise <= 0:
            pen = QPen(QColor("#1e293b"), outer_radius - inner_radius)
            pen.setCapStyle(Qt.FlatCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            mid_r = (outer_radius + inner_radius) / 2.0
            mid_rect = QRectF(cx - mid_r, cy - mid_r, mid_r * 2, mid_r * 2)
            painter.drawEllipse(mid_rect)

            painter.setPen(QColor("#64748b"))
            f = painter.font()
            f.setPointSize(10)
            f.setBold(False)
            painter.setFont(f)
            painter.drawText(self.rect(), Qt.AlignCenter, "No Expense\nData")
            return

        # Draw Slices
        start_angle = 90.0  # Start from 12 o'clock
        gap_deg = 1.2 if len(self.slices) > 1 else 0.0

        for s in self.slices:
            span_angle = (s["percentage"] / 100.0) * 360.0
            actual_span = max(0.5, span_angle - gap_deg)

            path = QPainterPath()
            path.arcMoveTo(outer_rect, start_angle)
            path.arcTo(outer_rect, start_angle, -actual_span)
            path.arcTo(inner_rect, start_angle - actual_span, actual_span)
            path.closeSubpath()

            painter.fillPath(path, QBrush(QColor(s["color"])))
            start_angle -= span_angle

        # Center Text
        painter.setPen(QColor("#f8fafc"))
        font_val = QFont(painter.font().family(), 13, QFont.Bold)
        painter.setFont(font_val)
        val_text = format_inr(self.total_amount_paise)
        fm = QFontMetrics(font_val)
        val_w = fm.horizontalAdvance(val_text)
        painter.drawText(int(cx - val_w / 2), int(cy - 2), val_text)

        painter.setPen(QColor("#94a3b8"))
        font_sub = QFont(painter.font().family(), 9, QFont.Normal)
        painter.setFont(font_sub)
        fm_sub = QFontMetrics(font_sub)
        sub_w = fm_sub.horizontalAdvance(self.center_title)
        painter.drawText(int(cx - sub_w / 2), int(cy + 16), self.center_title)


class CashFlowTrendBarChart(QWidget):
    """Grouped modern bar chart comparing Income vs Expense over the last N months."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.trend_data: List[Dict[str, Any]] = []

    def set_data(self, trend_data: List[Dict[str, Any]]):
        self.trend_data = trend_data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w = self.width()
        h = self.height()
        pad_left = 64
        pad_right = 24
        pad_top = 36
        pad_bottom = 36

        chart_w = w - pad_left - pad_right
        chart_h = h - pad_top - pad_bottom

        if chart_w <= 40 or chart_h <= 40:
            return

        # Determine Maximum Value for Y-Axis
        max_paise = 1000000  # Default ₹10,000 baseline
        for item in self.trend_data:
            max_paise = max(max_paise, item.get("income_paise", 0), item.get("expense_paise", 0))

        # Add 15% headroom
        max_paise = int(max_paise * 1.15)

        # Draw Y-Axis Guide Lines & Labels
        grid_steps = 4
        pen_grid = QPen(QColor("#1e293b"), 1, Qt.DashLine)
        pen_axis = QPen(QColor("#334155"), 1)
        font_label = QFont(painter.font().family(), 9)
        painter.setFont(font_label)

        for i in range(grid_steps + 1):
            y_val = pad_top + chart_h - (i / grid_steps) * chart_h
            painter.setPen(pen_grid)
            painter.drawLine(int(pad_left), int(y_val), int(pad_left + chart_w), int(y_val))

            # Label
            val_paise = int((i / grid_steps) * max_paise)
            lbl = f"₹{val_paise // 100000}k" if val_paise >= 100000 else f"₹{val_paise // 100}"
            painter.setPen(QColor("#64748b"))
            painter.drawText(0, int(y_val - 8), int(pad_left - 8), 16, Qt.AlignRight | Qt.AlignVCenter, lbl)

        # Baseline
        painter.setPen(pen_axis)
        painter.drawLine(int(pad_left), int(pad_top + chart_h), int(pad_left + chart_w), int(pad_top + chart_h))

        # Draw Top Legend
        legend_x = int(pad_left + chart_w - 200)
        legend_y = 12
        # Income Legend Dot
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#14b8a6"))
        painter.drawRoundedRect(legend_x, legend_y + 3, 10, 10, 3, 3)
        painter.setPen(QColor("#94a3b8"))
        painter.drawText(legend_x + 15, legend_y + 12, "Income")

        # Expense Legend Dot
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#f43f5e"))
        painter.drawRoundedRect(legend_x + 85, legend_y + 3, 10, 10, 3, 3)
        painter.setPen(QColor("#94a3b8"))
        painter.drawText(legend_x + 100, legend_y + 12, "Expense")

        # Draw Grouped Bars
        n_groups = len(self.trend_data)
        if n_groups == 0:
            return

        group_width = chart_w / n_groups
        bar_width = min(22.0, (group_width - 16) / 2.0)

        for idx, item in enumerate(self.trend_data):
            gx = pad_left + idx * group_width
            group_center_x = gx + group_width / 2.0

            inc = item.get("income_paise", 0)
            exp = item.get("expense_paise", 0)

            inc_h = (inc / max_paise) * chart_h
            exp_h = (exp / max_paise) * chart_h

            x_inc = group_center_x - bar_width - 2
            y_inc = pad_top + chart_h - inc_h

            x_exp = group_center_x + 2
            y_exp = pad_top + chart_h - exp_h

            # Income Bar Gradient
            if inc > 0:
                grad_inc = QLinearGradient(x_inc, y_inc, x_inc, pad_top + chart_h)
                grad_inc.setColorAt(0, QColor("#14b8a6"))
                grad_inc.setColorAt(1, QColor("#0d9488"))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(grad_inc))
                painter.drawRoundedRect(QRectF(x_inc, y_inc, bar_width, inc_h), 4, 4)

            # Expense Bar Gradient
            if exp > 0:
                grad_exp = QLinearGradient(x_exp, y_exp, x_exp, pad_top + chart_h)
                grad_exp.setColorAt(0, QColor("#f43f5e"))
                grad_exp.setColorAt(1, QColor("#e11d48"))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(grad_exp))
                painter.drawRoundedRect(QRectF(x_exp, y_exp, bar_width, exp_h), 4, 4)

            # X-Axis Month Label
            month_text = item.get("month_short", "")
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(
                int(gx), int(pad_top + chart_h + 8), int(group_width), 20,
                Qt.AlignCenter, month_text
            )


class SavingsHealthGauge(QWidget):
    """Modern Radial Arc Gauge displaying Family Savings Rate & Financial Health Status."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.savings_rate: float = 0.0
        self.status_text: str = "Healthy"
        self.status_color: str = "#10b981"

    def set_rate(self, rate_pct: float):
        self.savings_rate = rate_pct
        if rate_pct >= 30.0:
            self.status_text = "★ High Savings"
            self.status_color = "#10b981"
        elif rate_pct >= 15.0:
            self.status_text = "✔ Healthy Pace"
            self.status_color = "#14b8a6"
        elif rate_pct >= 0.0:
            self.status_text = "▲ Moderate Reserve"
            self.status_color = "#f59e0b"
        else:
            self.status_text = "⚠ Net Deficit"
            self.status_color = "#ef4444"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h * 0.58
        r = min(w / 2.0, h * 0.58) - 18.0
        if r <= 15:
            return

        arc_rect = QRectF(cx - r, cy - r, r * 2, r * 2)
        track_width = 12.0

        # Background Track Arc: from 210 deg down to -30 deg (240 degree span)
        start_angle = 210.0
        total_span = 240.0

        pen_bg = QPen(QColor("#1e293b"), track_width)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(arc_rect, int(start_angle * 16), int(-total_span * 16))

        # Active Rate Arc
        bounded_pct = max(0.0, min(100.0, self.savings_rate))
        active_span = (bounded_pct / 100.0) * total_span

        if active_span > 0:
            pen_active = QPen(QColor(self.status_color), track_width)
            pen_active.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_active)
            painter.drawArc(arc_rect, int(start_angle * 16), int(-active_span * 16))

        # Center Percentage Text
        painter.setPen(QColor("#f8fafc"))
        font_pct = QFont(painter.font().family(), 18, QFont.Bold)
        painter.setFont(font_pct)
        rate_str = f"{self.savings_rate:.1f}%"
        fm = QFontMetrics(font_pct)
        rw = fm.horizontalAdvance(rate_str)
        painter.drawText(int(cx - rw / 2), int(cy - 4), rate_str)

        # Label: Savings Rate
        painter.setPen(QColor("#94a3b8"))
        font_lbl = QFont(painter.font().family(), 9)
        painter.setFont(font_lbl)
        lbl_text = "Family Savings Rate"
        fm_lbl = QFontMetrics(font_lbl)
        lw = fm_lbl.horizontalAdvance(lbl_text)
        painter.drawText(int(cx - lw / 2), int(cy + 16), lbl_text)

        # Pill Status Badge below
        badge_w = 130
        badge_h = 24
        badge_x = int(cx - badge_w / 2)
        badge_y = int(cy + 30)

        # Background Pill
        painter.setPen(Qt.NoPen)
        bg_col = QColor(self.status_color)
        bg_col.setAlpha(35)
        painter.setBrush(QBrush(bg_col))
        painter.drawRoundedRect(badge_x, badge_y, badge_w, badge_h, 12, 12)

        # Text inside Pill
        painter.setPen(QColor(self.status_color))
        font_badge = QFont(painter.font().family(), 8, QFont.Bold)
        painter.setFont(font_badge)
        painter.drawText(badge_x, badge_y, badge_w, badge_h, Qt.AlignCenter, self.status_text)


class MemberSpendingSegmentedBar(QWidget):
    """Segmented multi-color horizontal proportion bar for family member attribution."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(18)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.segments: List[Dict[str, Any]] = []

    def set_data(self, member_data: List[Dict[str, Any]], total_paise: int):
        self.segments = []
        if total_paise > 0:
            for idx, m in enumerate(member_data):
                color = CHART_PALETTE[idx % len(CHART_PALETTE)]
                pct = (m["amount_paise"] / total_paise) * 100.0
                self.segments.append({
                    "name": m.get("user", m.get("name", "Unknown")),
                    "amount_paise": m["amount_paise"],
                    "pct": pct,
                    "color": color
                })
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        bar_rect = QRectF(0, 0, w, h)

        if not self.segments:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#1e293b"))
            painter.drawRoundedRect(bar_rect, 6, 6)
            return

        # Clip rounded rect
        clip_path = QPainterPath()
        clip_path.addRoundedRect(bar_rect, 6, 6)
        painter.setClipPath(clip_path)

        curr_x = 0.0
        for s in self.segments:
            seg_w = (s["pct"] / 100.0) * w
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(s["color"]))
            painter.drawRect(QRectF(curr_x, 0, seg_w + 1, h))
            curr_x += seg_w
