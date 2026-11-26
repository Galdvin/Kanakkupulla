"""
Investments View:
Comprehensive portfolio tracker displaying asset class breakdown,
unrealized gains, ROI %, and individual holding performance.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from core.investment_service import InvestmentService
from core.family_service import FamilyService
from ui.investments.investment_dialog import InvestmentDialog, UpdateValuationDialog
from ui.table_helper import configure_fintech_table

class InvestmentsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)

        # Header bar
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Investments & Wealth Portfolio")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #f8fafc;")
        sub_lbl = QLabel("Track mutual funds, equities, gold, and fixed deposits across all family members.")
        sub_lbl.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Member Filter
        self.member_combo = QComboBox()
        self.member_combo.addItem("All Family Holdings", None)
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

        # Update Valuation Button
        val_btn = QPushButton("📈 Update Valuation")
        val_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f766e; color: white; font-weight: 600;
                padding: 8px 16px; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #0d9488; }
        """)
        val_btn.clicked.connect(self.open_valuation_dialog)
        header_layout.addWidget(val_btn)

        # Add Investment Button
        add_btn = QPushButton("+ Add Investment")
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

        # Asset Class Pills Row
        self.pills_container = QFrame()
        self.pills_container.setStyleSheet("background-color: #1e293b; border-radius: 8px; padding: 10px 14px; border: 1px solid #334155;")
        self.pills_layout = QHBoxLayout(self.pills_container)
        self.pills_layout.setContentsMargins(4, 4, 4, 4)
        self.layout.addWidget(self.pills_container)

        # Holdings Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Asset Name", "Owner", "Asset Class", "Invested (₹)",
            "Current Value (₹)", "Gain / Loss", "Valuation Date", "Actions"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        inv_widths = {0: 180, 1: 120, 2: 120, 3: 130, 4: 130, 5: 120, 6: 110, 7: 90}
        configure_fintech_table(self.table, stretch_col=0, col_widths=inv_widths)
        self.layout.addWidget(self.table)

        self.load_data()

    def open_add_dialog(self):
        dlg = InvestmentDialog(self)
        if dlg.exec():
            self.load_data()

    def open_valuation_dialog(self, inv_id: Optional[int] = None):
        dlg = UpdateValuationDialog(preselected_inv_id=inv_id, parent=self)
        if dlg.exec():
            self.load_data()

    def load_data(self):
        # Clear KPIs
        while self.kpi_layout.count():
            item = self.kpi_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear Pills
        while self.pills_layout.count():
            item = self.pills_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        selected_member_id = self.member_combo.currentData()
        summary = InvestmentService.get_portfolio_summary(selected_member_id)
        investments = InvestmentService.get_all_investments(selected_member_id)

        gain_paise = summary["unrealized_gain_paise"]
        gain_color = "#10b981" if gain_paise >= 0 else "#f43f5e"
        gain_prefix = "+" if gain_paise >= 0 else ""

        self._add_kpi_card("Total Invested", f"₹{summary['total_invested_paise'] / 100:,.2f}", "#38bdf8")
        self._add_kpi_card("Portfolio Value", f"₹{summary['total_current_paise'] / 100:,.2f}", "#06b6d4")
        self._add_kpi_card("Unrealized Gain / Loss", f"{gain_prefix}₹{gain_paise / 100:,.2f}", gain_color)
        self._add_kpi_card("Total ROI", f"{gain_prefix}{summary['returns_pct']}%", gain_color)

        # Asset Class Pills
        alloc = summary.get("asset_allocation", {})
        if alloc:
            lbl_title = QLabel("Allocation: ")
            lbl_title.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 12px;")
            self.pills_layout.addWidget(lbl_title)
            for cls_name, val_paise in alloc.items():
                pct = (val_paise / summary["total_current_paise"] * 100) if summary["total_current_paise"] > 0 else 0
                pill = QLabel(f"{cls_name}: ₹{val_paise / 100:,.0f} ({pct:.0f}%)")
                pill.setStyleSheet("background-color: #0f172a; color: #cbd5e1; padding: 4px 10px; border-radius: 12px; font-size: 11px;")
                self.pills_layout.addWidget(pill)
            self.pills_layout.addStretch()
        else:
            empty_pill = QLabel("No holdings to display asset breakdown.")
            empty_pill.setStyleSheet("color: #64748b; font-size: 12px;")
            self.pills_layout.addWidget(empty_pill)
            self.pills_layout.addStretch()

        # Populate Table
        self.table.setRowCount(len(investments))
        for row, inv in enumerate(investments):
            # Name
            self.table.setItem(row, 0, QTableWidgetItem(inv.investment_name))

            # Owner
            owner_name = inv.family_member.name if inv.family_member else "Family"
            self.table.setItem(row, 1, QTableWidgetItem(f"👤 {owner_name}"))

            # Asset Type
            self.table.setItem(row, 2, QTableWidgetItem(inv.investment_type))

            # Invested
            inv_item = QTableWidgetItem(f"₹{inv.invested_amount_paise / 100:,.2f}")
            inv_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, inv_item)

            # Current
            curr_item = QTableWidgetItem(f"₹{inv.current_value_paise / 100:,.2f}")
            curr_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, curr_item)

            # Gain / Loss
            g_paise = inv.current_value_paise - inv.invested_amount_paise
            pct_g = (g_paise / inv.invested_amount_paise * 100) if inv.invested_amount_paise > 0 else 0
            g_str = f"{'+' if g_paise >= 0 else ''}₹{g_paise / 100:,.2f} ({pct_g:+.1f}%)"
            gain_item = QTableWidgetItem(g_str)
            gain_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            gain_item.setForeground(Qt.green if g_paise >= 0 else Qt.red)
            self.table.setItem(row, 5, gain_item)

            # Valuation Date
            val_date_str = inv.last_valuation_date.strftime("%d-%m-%Y") if inv.last_valuation_date else "-"
            self.table.setItem(row, 6, QTableWidgetItem(val_date_str))

            # Actions Widget
            action_widget = QWidget()
            a_lay = QHBoxLayout(action_widget)
            a_lay.setContentsMargins(4, 2, 4, 2)
            a_lay.setSpacing(6)

            edit_btn = QPushButton("Valuate")
            edit_btn.setStyleSheet("background-color: #0284c7; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;")
            edit_btn.clicked.connect(lambda _, i_id=inv.id: self.open_valuation_dialog(i_id))
            a_lay.addWidget(edit_btn)

            del_btn = QPushButton("✕")
            del_btn.setStyleSheet("background-color: #334155; color: #94a3b8; padding: 2px 8px; border-radius: 4px; font-weight: bold;")
            del_btn.clicked.connect(lambda _, i_id=inv.id: self.delete_investment(i_id))
            a_lay.addWidget(del_btn)

            self.table.setCellWidget(row, 7, action_widget)

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

    def delete_investment(self, inv_id: int):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to remove this investment holding?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = InvestmentService.delete_investment(inv_id)
            if success:
                self.load_data()
            else:
                QMessageBox.critical(self, "Error", msg)
