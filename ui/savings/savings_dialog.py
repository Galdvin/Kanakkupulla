"""
Savings Dialogs:
- SavingsGoalDialog: Create family/member financial goals.
- SavingsContributionDialog: Deposit funds towards an active savings goal.
"""
from typing import Optional
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QDateEdit, QPushButton, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt, QDate
from core.family_service import FamilyService
from core.account_service import AccountService
from core.savings_service import SavingsService
from config.constants import GoalPriority

class SavingsGoalDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Savings Goal")
        self.setFixedSize(480, 560)
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; color: #f8fafc; }
            QLabel { color: #94a3b8; font-size: 13px; font-weight: 500; }
            QLineEdit, QComboBox, QDateEdit, QTextEdit {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 6px; padding: 8px 12px; color: #f8fafc; font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
                border: 1px solid #0ea5e9;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("New Financial Goal")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(title)

        # Goal Name
        layout.addWidget(QLabel("Goal Name *"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. 6-Month Emergency Fund, Ooty Vacation")
        layout.addWidget(self.name_input)

        # Member
        layout.addWidget(QLabel("Family Member *"))
        self.member_combo = QComboBox()
        members = FamilyService.get_all_members()
        for m in members:
            self.member_combo.addItem(f"👤 {m.name} ({m.relation_type})", m.id)
        layout.addWidget(self.member_combo)

        # Target Amount
        layout.addWidget(QLabel("Target Savings Amount (₹) *"))
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("e.g. 200000")
        layout.addWidget(self.target_input)

        # Target Date
        row_dates = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Target Date *"))
        self.target_date_edit = QDateEdit()
        self.target_date_edit.setCalendarPopup(True)
        # Default 1 year from now
        t = date.today()
        self.target_date_edit.setDate(QDate(t.year + 1, t.month, t.day))
        v1.addWidget(self.target_date_edit)
        row_dates.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Priority"))
        self.priority_combo = QComboBox()
        for p in [GoalPriority.LOW, GoalPriority.MEDIUM, GoalPriority.HIGH, GoalPriority.CRITICAL]:
            self.priority_combo.addItem(p.value, p.value)
        self.priority_combo.setCurrentText(GoalPriority.MEDIUM.value)
        v2.addWidget(self.priority_combo)
        row_dates.addLayout(v2)
        layout.addLayout(row_dates)

        # Monthly planned contribution
        layout.addWidget(QLabel("Target Monthly Contribution (₹)"))
        self.monthly_input = QLineEdit()
        self.monthly_input.setPlaceholderText("e.g. 15000 (Optional)")
        layout.addWidget(self.monthly_input)

        # Notes
        layout.addWidget(QLabel("Notes (Optional)"))
        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(60)
        layout.addWidget(self.notes_input)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #334155; color: #f8fafc; padding: 9px 18px; border-radius: 6px;")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Goal")
        save_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: 600; padding: 9px 18px; border-radius: 6px;")
        save_btn.clicked.connect(self.save)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Goal name is required.")
            return

        member_id = self.member_combo.currentData()
        if not member_id:
            QMessageBox.warning(self, "Validation Error", "Please select a family member.")
            return

        try:
            target_rupees = float(self.target_input.text().strip() or "0")
            if target_rupees <= 0:
                raise ValueError()
            target_paise = int(round(target_rupees * 100))
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid target amount.")
            return

        monthly_paise = 0
        if self.monthly_input.text().strip():
            try:
                monthly_paise = int(round(float(self.monthly_input.text().strip()) * 100))
            except ValueError:
                pass

        t_date = self.target_date_edit.date()
        target_d = date(t_date.year(), t_date.month(), t_date.day())
        priority = self.priority_combo.currentText()
        notes = self.notes_input.toPlainText().strip() or None

        success, msg, _ = SavingsService.create_goal(
            family_member_id=member_id,
            goal_name=name,
            target_amount_paise=target_paise,
            start_date=date.today(),
            target_date=target_d,
            monthly_contribution_paise=monthly_paise,
            priority=priority,
            notes=notes
        )

        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save goal: {msg}")


class SavingsContributionDialog(QDialog):
    def __init__(self, preselected_goal_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Savings Contribution")
        self.setFixedSize(440, 440)
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; color: #f8fafc; }
            QLabel { color: #94a3b8; font-size: 13px; font-weight: 500; }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 6px; padding: 8px 12px; color: #f8fafc; font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus { border: 1px solid #0ea5e9; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Add Contribution to Goal")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #10b981;")
        layout.addWidget(title)

        # Goal selector
        layout.addWidget(QLabel("Target Savings Goal *"))
        self.goal_combo = QComboBox()
        goals = SavingsService.get_all_goals()
        for g in goals:
            member_tag = f"({g.family_member.name})" if g.family_member else ""
            self.goal_combo.addItem(f"{g.goal_name} {member_tag} - Target: ₹{g.target_amount_paise/100:,.0f}", g.id)
            if preselected_goal_id and g.id == preselected_goal_id:
                self.goal_combo.setCurrentIndex(self.goal_combo.count() - 1)
        layout.addWidget(self.goal_combo)

        # Deposit Amount
        layout.addWidget(QLabel("Contribution Amount (₹) *"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("e.g. 5000")
        layout.addWidget(self.amount_input)

        # Source Account
        layout.addWidget(QLabel("Deduct From Account (Optional)"))
        self.account_combo = QComboBox()
        self.account_combo.addItem("None (External or Cash savings)", None)
        accounts = AccountService.get_all_accounts()
        for a in accounts:
            self.account_combo.addItem(f"{a.name} (Bal: ₹{a.current_balance_paise/100:,.2f})", a.id)
        layout.addWidget(self.account_combo)

        # Date
        layout.addWidget(QLabel("Contribution Date"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        today = date.today()
        self.date_edit.setDate(QDate(today.year, today.month, today.day))
        layout.addWidget(self.date_edit)

        # Notes
        layout.addWidget(QLabel("Notes / Reference"))
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("e.g. Salary bonus deposit")
        layout.addWidget(self.notes_input)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #334155; color: #f8fafc; padding: 9px 18px; border-radius: 6px;")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Record Deposit")
        save_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: 600; padding: 9px 18px; border-radius: 6px;")
        save_btn.clicked.connect(self.save)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def save(self):
        goal_id = self.goal_combo.currentData()
        if not goal_id:
            QMessageBox.warning(self, "Validation Error", "No savings goal selected.")
            return

        try:
            amt_rupees = float(self.amount_input.text().strip() or "0")
            if amt_rupees <= 0:
                raise ValueError()
            amt_paise = int(round(amt_rupees * 100))
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid positive deposit amount.")
            return

        q_d = self.date_edit.date()
        c_date = date(q_d.year(), q_d.month(), q_d.day())
        acc_id = self.account_combo.currentData()
        notes = self.notes_input.text().strip() or None

        success, msg = SavingsService.record_contribution(
            goal_id=goal_id,
            amount_paise=amt_paise,
            contribution_date=c_date,
            account_id=acc_id,
            notes=notes
        )

        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to record contribution: {msg}")
