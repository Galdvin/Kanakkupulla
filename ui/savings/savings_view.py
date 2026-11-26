"""
Savings Goals View:
Displays visual progress cards for emergency funds, major family purchases,
and individual savings targets with deposit actions.
"""
from typing import Optional
from datetime import date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QScrollArea, QFrame, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt
from core.savings_service import SavingsService
from core.family_service import FamilyService
from ui.savings.savings_dialog import SavingsGoalDialog, SavingsContributionDialog

class SavingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)

        # Header bar
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Savings Goals & Milestones")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #f8fafc;")
        sub_lbl = QLabel("Build emergency reserves, plan for big events, and watch your family wealth grow.")
        sub_lbl.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Member Filter
        self.member_combo = QComboBox()
        self.member_combo.addItem("All Family Members", None)
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

        # Deposit Button
        deposit_btn = QPushButton("💰 Add Deposit")
        deposit_btn.setCursor(Qt.PointingHandCursor)
        deposit_btn.setFixedHeight(36)
        deposit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
                color: white; font-weight: 700;
                padding: 6px 16px; border-radius: 8px; font-size: 13px;
                border: 1px solid #34d399;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #34d399);
                color: #0f172a;
            }
        """)
        deposit_btn.clicked.connect(self.open_deposit_dialog)
        header_layout.addWidget(deposit_btn)

        # Add Goal Button
        add_btn = QPushButton("+ New Goal")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedHeight(36)
        add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f766e, stop:1 #14b8a6);
                color: white; font-weight: 700;
                padding: 6px 16px; border-radius: 8px; font-size: 13px;
                border: 1px solid #2dd4bf;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #14b8a6, stop:1 #2dd4bf);
                color: #0f172a;
            }
        """)
        add_btn.clicked.connect(self.open_add_goal_dialog)
        header_layout.addWidget(add_btn)

        self.layout.addLayout(header_layout)

        # KPI Summary Cards
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(16)
        self.layout.addLayout(self.kpi_layout)

        # Scroll Area for Goal Cards
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

    def open_add_goal_dialog(self):
        dlg = SavingsGoalDialog(self)
        if dlg.exec():
            self.load_data()

    def open_deposit_dialog(self, goal_id: Optional[int] = None):
        goals = SavingsService.get_all_goals()
        if not goals:
            reply = QMessageBox.question(
                self, "No Active Savings Goals",
                "You haven't created any savings goals yet.\n\nWould you like to create a new goal first?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.open_add_goal_dialog()
            return
        dlg = SavingsContributionDialog(preselected_goal_id=goal_id, parent=self)
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
        summary = SavingsService.get_savings_summary(selected_member_id)
        goals = SavingsService.get_all_goals(selected_member_id)

        self._add_kpi_card("Total Target Sum", f"₹{summary['total_target_paise'] / 100:,.2f}", "#38bdf8")
        self._add_kpi_card("Current Accumulated", f"₹{summary['total_saved_paise'] / 100:,.2f}", "#10b981")
        self._add_kpi_card("Remaining to Goal", f"₹{summary['remaining_paise'] / 100:,.2f}", "#f59e0b")
        self._add_kpi_card("Overall Progress", f"{summary['progress_pct']}%", "#06b6d4")

        if not goals:
            empty_lbl = QLabel("No savings goals found. Click '+ New Goal' to begin planning your financial targets.")
            empty_lbl.setStyleSheet("color: #64748b; font-size: 14px; padding: 40px; font-weight: 500;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(empty_lbl)
            return

        for g in goals:
            self._add_goal_card(g)

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

    def _add_goal_card(self, g):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 16px;
            }
        """)
        lay = QVBoxLayout(card)
        lay.setSpacing(12)

        # Header: Name, Member, Priority, Status, Delete
        top_row = QHBoxLayout()
        name_lbl = QLabel(g.goal_name)
        name_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc;")
        top_row.addWidget(name_lbl)

        member_name = g.family_member.name if g.family_member else "Family"
        member_badge = QLabel(f"👤 {member_name}")
        member_badge.setStyleSheet("background-color: #0f172a; color: #38bdf8; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;")
        top_row.addWidget(member_badge)

        priority_colors = {
            "Critical": ("#881337", "#f43f5e"),
            "High": ("#78350f", "#fbbf24"),
            "Medium": ("#065f46", "#34d399"),
            "Low": ("#1e293b", "#94a3b8")
        }
        bg_col, txt_col = priority_colors.get(g.priority, ("#334155", "#94a3b8"))
        prio_badge = QLabel(g.priority.upper())
        prio_badge.setStyleSheet(f"background-color: {bg_col}; color: {txt_col}; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700;")
        top_row.addWidget(prio_badge)

        if g.is_completed:
            done_badge = QLabel("✓ COMPLETED")
            done_badge.setStyleSheet("background-color: #065f46; color: #34d399; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700;")
            top_row.addWidget(done_badge)

        top_row.addStretch()

        deposit_btn = QPushButton("+ Deposit")
        deposit_btn.setStyleSheet("background-color: #0f766e; color: #f8fafc; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 4px;")
        deposit_btn.clicked.connect(lambda _, g_id=g.id: self.open_deposit_dialog(g_id))
        top_row.addWidget(deposit_btn)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet("QPushButton { background-color: #334155; color: #94a3b8; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #ef4444; color: white; }")
        del_btn.clicked.connect(lambda _, g_id=g.id: self.delete_goal(g_id))
        top_row.addWidget(del_btn)

        lay.addLayout(top_row)

        # Dates & target
        days_left = (g.target_date - date.today()).days
        time_desc = f"{days_left} days remaining" if days_left > 0 else ("Target date reached" if days_left == 0 else f"{abs(days_left)} days overdue")
        sub_row = QLabel(f"Target Date: {g.target_date.strftime('%d-%m-%Y')} ({time_desc})")
        sub_row.setStyleSheet("color: #64748b; font-size: 12px;")
        lay.addWidget(sub_row)

        # Progress stats
        pct = (g.current_amount_paise / g.target_amount_paise * 100) if g.target_amount_paise > 0 else 0
        amt_row = QHBoxLayout()
        saved_lbl = QLabel(f"Saved: ₹{g.current_amount_paise / 100:,.2f}")
        saved_lbl.setStyleSheet("font-weight: 700; color: #10b981; font-size: 14px;")
        target_lbl = QLabel(f"Target: ₹{g.target_amount_paise / 100:,.2f}")
        target_lbl.setStyleSheet("color: #94a3b8; font-size: 14px;")
        pct_lbl = QLabel(f"{pct:.1f}%")
        pct_lbl.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 14px;")

        amt_row.addWidget(saved_lbl)
        amt_row.addWidget(target_lbl)
        amt_row.addStretch()
        amt_row.addWidget(pct_lbl)
        lay.addLayout(amt_row)

        # Progress bar
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(min(100, int(pct)))
        bar.setTextVisible(False)
        bar.setFixedHeight(8)
        bar.setStyleSheet("""
            QProgressBar {
                background-color: #0f172a; border: none; border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #10b981; border-radius: 4px;
            }
        """)
        lay.addWidget(bar)

        if g.notes:
            notes_lbl = QLabel(f"Note: {g.notes}")
            notes_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-style: italic;")
            lay.addWidget(notes_lbl)

        self.cards_layout.addWidget(card)

    def delete_goal(self, goal_id: int):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this savings goal?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = SavingsService.delete_goal(goal_id)
            if success:
                self.load_data()
            else:
                QMessageBox.critical(self, "Error", msg)
