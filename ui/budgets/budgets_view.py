"""
Budgets View:
Visual budget planning cards with multi-tier alert thresholds (Normal, Caution, Warning, Exceeded),
family member filters, and category breakdown.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QScrollArea, QFrame, QProgressBar, QMessageBox, QGridLayout
)
from PySide6.QtCore import Qt
from core.budget_service import BudgetService, BudgetAlertLevel
from core.family_service import FamilyService
from ui.budgets.budget_dialog import BudgetDialog

class BudgetsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)

        # Header bar
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Budgets & Spending Limits")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #f8fafc;")
        sub_lbl = QLabel("Plan monthly caps, monitor category burn rates, and prevent family overspending.")
        sub_lbl.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Member Filter
        self.member_combo = QComboBox()
        self.member_combo.addItem("All Budgets (Family & Members)", None)
        members = FamilyService.get_all_members()
        for m in members:
            self.member_combo.addItem(f"👤 {m.name}", m.id)
        self.member_combo.currentIndexChanged.connect(self.load_data)
        self.member_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 6px; padding: 6px 12px; color: #f8fafc; font-size: 13px;
            }
        """)
        header_layout.addWidget(self.member_combo)

        # Add Budget Button
        add_btn = QPushButton("+ Create New Budget")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; color: white; font-weight: 600;
                padding: 8px 16px; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        add_btn.clicked.connect(self.open_add_dialog)
        header_layout.addWidget(add_btn)

        self.layout.addLayout(header_layout)

        # KPI Summary Cards
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(16)
        self.layout.addLayout(self.kpi_layout)

        # Scroll Area for Budget Cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(14)
        self.cards_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.cards_container)
        self.layout.addWidget(self.scroll_area)

        self.load_data()

    def open_add_dialog(self):
        dlg = BudgetDialog(self)
        if dlg.exec():
            self.load_data()

    def load_data(self):
        # Clear existing KPIs
        while self.kpi_layout.count():
            item = self.kpi_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        selected_member_id = self.member_combo.currentData()
        budgets = BudgetService.get_all_budgets(selected_member_id)

        # Calculate KPIs
        total_budgeted_paise = 0
        total_spent_paise = 0
        for b in budgets:
            st = BudgetService.get_budget_status(b.id)
            if st:
                total_budgeted_paise += st["total_budget_paise"]
                total_spent_paise += st["total_spent_paise"]

        rem_paise = total_budgeted_paise - total_spent_paise
        overall_util = (total_spent_paise / total_budgeted_paise * 100) if total_budgeted_paise > 0 else 0

        self._add_kpi_card("Total Budget Cap", f"₹{total_budgeted_paise / 100:,.2f}", "#38bdf8")
        self._add_kpi_card("Total Spent", f"₹{total_spent_paise / 100:,.2f}", "#f43f5e")
        self._add_kpi_card("Remaining Buffer", f"₹{max(0, rem_paise) / 100:,.2f}", "#10b981")
        self._add_kpi_card("Overall Burn Rate", f"{overall_util:.1f}%", "#f59e0b" if overall_util > 75 else "#06b6d4")

        if not budgets:
            empty_lbl = QLabel("No active budgets found. Click '+ Create New Budget' to define your spending targets.")
            empty_lbl.setStyleSheet("color: #64748b; font-size: 14px; padding: 40px; font-weight: 500;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(empty_lbl)
            return

        for b in budgets:
            st = BudgetService.get_budget_status(b.id)
            if st:
                self._add_budget_card(st)

    def _add_kpi_card(self, title: str, value: str, val_color: str):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 14px;
            }
        """)
        lay = QVBoxLayout(card)
        lay.setSpacing(4)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600; text-transform: uppercase;")
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(f"color: {val_color}; font-size: 20px; font-weight: 700;")
        lay.addWidget(t_lbl)
        lay.addWidget(v_lbl)
        self.kpi_layout.addWidget(card)

    def _add_budget_card(self, st: dict):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 16px;
            }
        """)
        lay = QVBoxLayout(card)
        lay.setSpacing(12)

        # Header row: Name, Scope, Alert Badge, Delete
        top_row = QHBoxLayout()
        name_lbl = QLabel(st["name"])
        name_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc;")
        top_row.addWidget(name_lbl)

        scope_badge = QLabel(f"👤 {st['member_name']}")
        scope_badge.setStyleSheet("background-color: #0f172a; color: #38bdf8; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;")
        top_row.addWidget(scope_badge)

        top_row.addStretch()

        # Alert Badge
        alert_colors = {
            BudgetAlertLevel.NORMAL: ("#065f46", "#34d399"),
            BudgetAlertLevel.CAUTION: ("#78350f", "#fbbf24"),
            BudgetAlertLevel.WARNING: ("#7c2d12", "#fb923c"),
            BudgetAlertLevel.EXCEEDED: ("#881337", "#f43f5e")
        }
        bg_col, txt_col = alert_colors.get(st["alert_level"], ("#334155", "#94a3b8"))
        alert_badge = QLabel(st["alert_level"].upper())
        alert_badge.setStyleSheet(f"background-color: {bg_col}; color: {txt_col}; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 700;")
        top_row.addWidget(alert_badge)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet("QPushButton { background-color: #334155; color: #94a3b8; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #ef4444; color: white; }")
        del_btn.clicked.connect(lambda _, b_id=st["budget_id"]: self.delete_budget(b_id))
        top_row.addWidget(del_btn)
        lay.addLayout(top_row)

        # Sub-info row: Dates & Period
        dates_lbl = QLabel(f"Period: {st['period_type']}  |  {st['start_date'].strftime('%d-%m-%Y')} to {st['end_date'].strftime('%d-%m-%Y')}")
        dates_lbl.setStyleSheet("color: #64748b; font-size: 12px;")
        lay.addWidget(dates_lbl)

        # Amount Details Row
        amt_row = QHBoxLayout()
        spent_str = f"Spent: ₹{st['total_spent_paise'] / 100:,.2f}"
        cap_str = f"Cap: ₹{st['total_budget_paise'] / 100:,.2f}"
        rem_str = f"Remaining: ₹{st['remaining_paise'] / 100:,.2f}" if st['remaining_paise'] >= 0 else f"Over by: ₹{abs(st['remaining_paise']) / 100:,.2f}"

        s_lbl = QLabel(spent_str)
        s_lbl.setStyleSheet("font-weight: 600; color: #f8fafc;")
        c_lbl = QLabel(cap_str)
        c_lbl.setStyleSheet("color: #94a3b8;")
        r_lbl = QLabel(rem_str)
        r_lbl.setStyleSheet("font-weight: 600; color: #34d399;" if st['remaining_paise'] >= 0 else "font-weight: 600; color: #f43f5e;")

        amt_row.addWidget(s_lbl)
        amt_row.addWidget(c_lbl)
        amt_row.addStretch()
        amt_row.addWidget(r_lbl)
        amt_row.addWidget(QLabel(f"({st['utilization_pct']}%)"))
        lay.addLayout(amt_row)

        # Progress Bar
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(min(100, int(st["utilization_pct"])))
        bar.setTextVisible(False)
        bar.setFixedHeight(8)

        bar_color = "#10b981"
        if st["alert_level"] == BudgetAlertLevel.CAUTION:
            bar_color = "#f59e0b"
        elif st["alert_level"] == BudgetAlertLevel.WARNING:
            bar_color = "#f97316"
        elif st["alert_level"] == BudgetAlertLevel.EXCEEDED:
            bar_color = "#ef4444"

        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #0f172a; border: none; border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {bar_color}; border-radius: 4px;
            }}
        """)
        lay.addWidget(bar)

        # Category Breakdown (if any allocated)
        if st.get("category_breakdown"):
            cat_box = QFrame()
            cat_box.setStyleSheet("background-color: #0f172a; border-radius: 6px; padding: 10px;")
            cat_lay = QVBoxLayout(cat_box)
            cat_lay.setSpacing(6)

            title_cat = QLabel("Category Allocations:")
            title_cat.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
            cat_lay.addWidget(title_cat)

            for cb in st["category_breakdown"]:
                crow = QHBoxLayout()
                cn = QLabel(cb["category_name"])
                cn.setStyleSheet("color: #cbd5e1; font-size: 12px;")
                cv = QLabel(f"₹{cb['spent_paise'] / 100:,.0f} / ₹{cb['allocated_paise'] / 100:,.0f} ({cb['utilization_pct']}%)")
                cv.setStyleSheet(f"font-size: 12px; font-weight: 500; color: {'#f43f5e' if cb['spent_paise'] > cb['allocated_paise'] else '#94a3b8'};")
                crow.addWidget(cn)
                crow.addStretch()
                crow.addWidget(cv)
                cat_lay.addLayout(crow)

            lay.addWidget(cat_box)

        self.cards_layout.addWidget(card)

    def delete_budget(self, budget_id: int):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this budget? Past transactions will remain intact.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = BudgetService.delete_budget(budget_id)
            if success:
                self.load_data()
            else:
                QMessageBox.critical(self, "Error", msg)
