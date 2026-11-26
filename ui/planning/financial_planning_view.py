"""
Financial Planning & Forecasting View:
Simulates cash runway, 12-month forward cash flows, inflation impacts,
and multi-year savings trajectories.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox,
    QLineEdit, QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from analytics.forecasting import ForecastingEngine
from ui.table_helper import configure_fintech_table, PLANNING_WIDTHS

class FinancialPlanningView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)

        # Header bar
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Financial Planning & Projections Engine")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #f8fafc;")
        sub_lbl = QLabel("Calculate cash runway buffer, stress-test inflation shocks, and simulate 12-month future balances.")
        sub_lbl.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.layout.addLayout(header_layout)

        # Top Cash Runway Banner
        self.runway_banner = QFrame()
        self.runway_banner.setStyleSheet("""
            QFrame {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 16px;
            }
        """)
        self.runway_layout = QHBoxLayout(self.runway_banner)
        self.layout.addWidget(self.runway_banner)

        # Assumptions Controls Bar
        assumptions_frame = QFrame()
        assumptions_frame.setStyleSheet("background-color: #0f172a; border-radius: 8px; padding: 12px 16px; border: 1px solid #334155;")
        assump_lay = QHBoxLayout(assumptions_frame)
        assump_lay.setSpacing(14)

        # Inflation input
        assump_lay.addWidget(QLabel("Annual Inflation (%):"))
        self.inflation_spin = QDoubleSpinBox()
        self.inflation_spin.setRange(0.0, 30.0)
        self.inflation_spin.setValue(6.0)
        self.inflation_spin.setSingleStep(0.5)
        self.inflation_spin.setStyleSheet("background-color: #1e293b; color: #f8fafc; padding: 6px; border-radius: 4px; border: 1px solid #334155;")
        assump_lay.addWidget(self.inflation_spin)

        # Income Growth input
        assump_lay.addWidget(QLabel("Income Growth (%):"))
        self.growth_spin = QDoubleSpinBox()
        self.growth_spin.setRange(0.0, 40.0)
        self.growth_spin.setValue(8.0)
        self.growth_spin.setSingleStep(0.5)
        self.growth_spin.setStyleSheet("background-color: #1e293b; color: #f8fafc; padding: 6px; border-radius: 4px; border: 1px solid #334155;")
        assump_lay.addWidget(self.growth_spin)

        # Custom Baseline Income
        assump_lay.addWidget(QLabel("Monthly Income (₹):"))
        self.income_input = QLineEdit()
        self.income_input.setPlaceholderText("Auto from history")
        self.income_input.setStyleSheet("background-color: #1e293b; color: #f8fafc; padding: 6px 10px; border-radius: 4px; border: 1px solid #334155; max-width: 140px;")
        assump_lay.addWidget(self.income_input)

        recalc_btn = QPushButton("🔄 Run Simulation")
        recalc_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: 600; padding: 7px 16px; border-radius: 6px;")
        recalc_btn.clicked.connect(self.load_data)
        assump_lay.addWidget(recalc_btn)
        assump_lay.addStretch()

        self.layout.addWidget(assumptions_frame)

        # 12-Month Projections Table
        table_title = QLabel("12-Month Forward Cash Flow Trajectory:")
        table_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #cbd5e1;")
        self.layout.addWidget(table_title)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Month", "Projected Income", "Fixed Obligations", "Variable Expenses",
            "Total Outflow", "Net Surplus / Savings", "Projected Bank Balance", "Savings Rate"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        configure_fintech_table(self.table, stretch_col=5, col_widths=PLANNING_WIDTHS)
        self.layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        # 1. Update Runway Banner
        runway_info = ForecastingEngine.get_cash_runway()
        while self.runway_layout.count():
            item = self.runway_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Left: Runway months & badge
        v_left = QVBoxLayout()
        v_left.setSpacing(4)
        runway_title = QLabel("CASH BUFFER RUNWAY")
        runway_title.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700;")
        runway_val = QLabel(f"{runway_info['runway_months']} Months")
        runway_val.setStyleSheet(f"color: {runway_info['health_color']}; font-size: 26px; font-weight: 800;")
        status_lbl = QLabel(f"● {runway_info['health_status']}")
        status_lbl.setStyleSheet(f"color: {runway_info['health_color']}; font-weight: 600; font-size: 12px;")
        v_left.addWidget(runway_title)
        v_left.addWidget(runway_val)
        v_left.addWidget(status_lbl)
        self.runway_layout.addLayout(v_left)

        self.runway_layout.addStretch()

        # Right: Details
        v_right = QVBoxLayout()
        v_right.setSpacing(4)
        liq_str = f"Liquid Reserves: ₹{runway_info['total_liquid_paise'] / 100:,.2f}"
        burn_str = f"Total Monthly Burn Rate: ₹{runway_info['total_monthly_burn_paise'] / 100:,.2f}"
        sub_burn = f"↳ Loan EMIs: ₹{runway_info['monthly_emi_paise']/100:,.0f} | Recurring: ₹{runway_info['monthly_recurring_paise']/100:,.0f} | Living: ₹{runway_info['monthly_variable_paise']/100:,.0f}"

        l_lbl = QLabel(liq_str)
        l_lbl.setStyleSheet("color: #38bdf8; font-size: 14px; font-weight: 700;")
        b_lbl = QLabel(burn_str)
        b_lbl.setStyleSheet("color: #f43f5e; font-size: 14px; font-weight: 700;")
        sb_lbl = QLabel(sub_burn)
        sb_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")

        v_right.addWidget(l_lbl)
        v_right.addWidget(b_lbl)
        v_right.addWidget(sb_lbl)
        self.runway_layout.addLayout(v_right)

        # 2. 12-Month Projections Simulation
        inf = self.inflation_spin.value()
        gr = self.growth_spin.value()

        custom_inc_paise = None
        if self.income_input.text().strip():
            try:
                custom_inc_paise = int(round(float(self.income_input.text().strip()) * 100))
            except ValueError:
                pass

        proj_data = ForecastingEngine.project_12_month_cashflow(
            annual_inflation_pct=inf,
            expected_income_growth_pct=gr,
            custom_monthly_income_paise=custom_inc_paise
        )

        projections = proj_data["monthly_projections"]
        self.table.setRowCount(len(projections))

        for row, p in enumerate(projections):
            # Month Label
            self.table.setItem(row, 0, QTableWidgetItem(p["month_label"]))

            # Income
            inc_it = QTableWidgetItem(f"₹{p['projected_income_paise'] / 100:,.0f}")
            inc_it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 1, inc_it)

            # Fixed Obligations
            fix_it = QTableWidgetItem(f"₹{p['fixed_obligations_paise'] / 100:,.0f}")
            fix_it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, fix_it)

            # Variable Expenses
            var_it = QTableWidgetItem(f"₹{p['variable_expenses_paise'] / 100:,.0f}")
            var_it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, var_it)

            # Total Outflow
            out_it = QTableWidgetItem(f"₹{p['total_expenses_paise'] / 100:,.0f}")
            out_it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            out_it.setForeground(Qt.red)
            self.table.setItem(row, 4, out_it)

            # Net Surplus
            net_val = p["net_savings_paise"]
            net_it = QTableWidgetItem(f"{'+' if net_val >= 0 else ''}₹{net_val / 100:,.0f}")
            net_it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            net_it.setForeground(Qt.green if net_val >= 0 else Qt.red)
            self.table.setItem(row, 5, net_it)

            # Cumulative Bank Balance
            bal_it = QTableWidgetItem(f"₹{p['cumulative_balance_paise'] / 100:,.0f}")
            bal_it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            bal_it.setForeground(Qt.cyan)
            self.table.setItem(row, 6, bal_it)

            # Savings Rate %
            rate_it = QTableWidgetItem(f"{p['savings_rate_pct']}%")
            rate_it.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 7, rate_it)
