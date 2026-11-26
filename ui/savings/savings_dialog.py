"""
Savings Dialogs:
- SavingsGoalDialog: Create family/member financial goals.
- SavingsContributionDialog: Deposit funds towards an active savings goal.
"""
from typing import Optional
from datetime import date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QDateEdit, QPushButton, QMessageBox, QTextEdit, QWidget
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
        self.resize(520, 650)
        self.setMinimumSize(480, 580)
        self.setStyleSheet("""
            QDialog { background-color: #0a0f1d; color: #f8fafc; }
            QLabel { color: #94a3b8; font-size: 13px; font-weight: 600; }
            QLineEdit, QComboBox, QDateEdit, QTextEdit {
                background-color: #111827; border: 1px solid #334155;
                border-radius: 8px; padding: 6px 12px; color: #f8fafc; font-size: 13px;
                min-height: 24px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
                border: 1px solid #14b8a6; background-color: #0d1322;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        # Header Title
        header_wrap = QWidget()
        header_layout = QVBoxLayout(header_wrap)
        header_layout.setContentsMargins(0, 0, 0, 4)
        header_layout.setSpacing(2)

        title = QLabel("🎯 New Financial Goal")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #2dd4bf;")
        header_layout.addWidget(title)

        sub_title = QLabel("Set family milestones and planned monthly deposits")
        sub_title.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 500;")
        header_layout.addWidget(sub_title)
        layout.addWidget(header_wrap)

        # Goal Name
        layout.addWidget(QLabel("Goal Name *"))
        self.name_input = QLineEdit()
        self.name_input.setFixedHeight(38)
        self.name_input.setPlaceholderText("e.g. 6-Month Emergency Fund, Ooty Vacation")
        layout.addWidget(self.name_input)

        # Member
        layout.addWidget(QLabel("Family Member *"))
        self.member_combo = QComboBox()
        self.member_combo.setCursor(Qt.PointingHandCursor)
        self.member_combo.setFixedHeight(38)
        members = FamilyService.get_all_members()
        if not members:
            self.member_combo.addItem("⚠️ No family members found", None)
        else:
            for m in members:
                name = m.name if m.name else "Member"
                self.member_combo.addItem(f"👤 {name} ({m.relation_type})", m.id)
        layout.addWidget(self.member_combo)

        # Target Amount
        layout.addWidget(QLabel("Target Savings Amount (₹) *"))
        self.target_input = QLineEdit()
        self.target_input.setFixedHeight(38)
        self.target_input.setPlaceholderText("e.g. 200000")
        layout.addWidget(self.target_input)

        # Target Date & Priority in clean QGridLayout (Prevents any overlap or merging)
        grid_row = QGridLayout()
        grid_row.setSpacing(10)
        grid_row.setContentsMargins(0, 0, 0, 0)
        
        lbl_date = QLabel("Target Date *")
        grid_row.addWidget(lbl_date, 0, 0)
        self.target_date_edit = QDateEdit()
        self.target_date_edit.setFixedHeight(38)
        self.target_date_edit.setCalendarPopup(True)
        t = date.today()
        self.target_date_edit.setDate(QDate(t.year + 1, t.month, t.day))
        grid_row.addWidget(self.target_date_edit, 1, 0)

        lbl_priority = QLabel("Priority")
        grid_row.addWidget(lbl_priority, 0, 1)
        self.priority_combo = QComboBox()
        self.priority_combo.setCursor(Qt.PointingHandCursor)
        self.priority_combo.setFixedHeight(38)
        for p in [GoalPriority.LOW, GoalPriority.MEDIUM, GoalPriority.HIGH, GoalPriority.CRITICAL]:
            self.priority_combo.addItem(f"⚡ {p.value}", p.value)
        self.priority_combo.setCurrentIndex(1) # Medium default
        grid_row.addWidget(self.priority_combo, 1, 1)

        layout.addLayout(grid_row)

        # Monthly planned contribution
        layout.addWidget(QLabel("Target Monthly Contribution (₹)"))
        self.monthly_input = QLineEdit()
        self.monthly_input.setFixedHeight(38)
        self.monthly_input.setPlaceholderText("e.g. 15000 (Optional)")
        layout.addWidget(self.monthly_input)

        # Notes
        layout.addWidget(QLabel("Notes (Optional)"))
        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(54)
        layout.addWidget(self.notes_input)

        layout.addSpacing(6)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b; color: #94a3b8;
                border: 1px solid #334155; padding: 8px 18px; border-radius: 8px; font-weight: 600;
            }
            QPushButton:hover { background-color: #334155; color: #f8fafc; }
        """)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Goal")
        save_btn.setFixedHeight(40)
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f766e, stop:1 #14b8a6);
                color: white; font-weight: 700; padding: 8px 22px; border-radius: 8px; border: 1px solid #2dd4bf;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #14b8a6, stop:1 #2dd4bf);
                color: #0f172a;
            }
        """)
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
        priority = self.priority_combo.currentData() or GoalPriority.MEDIUM.value
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
        self.resize(520, 580)
        self.setMinimumSize(480, 520)
        self.setStyleSheet("""
            QDialog { background-color: #0a0f1d; color: #f8fafc; }
            QLabel { color: #94a3b8; font-size: 13px; font-weight: 600; }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #111827; border: 1px solid #334155;
                border-radius: 8px; padding: 6px 12px; color: #f8fafc; font-size: 13px;
                min-height: 24px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #14b8a6; background-color: #0d1322;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(11)
        layout.setContentsMargins(24, 20, 24, 20)

        # Header Title
        header_wrap = QWidget()
        header_layout = QVBoxLayout(header_wrap)
        header_layout.setContentsMargins(0, 0, 0, 4)
        header_layout.setSpacing(2)

        title = QLabel("💰 Add Contribution to Goal")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #10b981;")
        header_layout.addWidget(title)

        sub_title = QLabel("Allocate funds towards an active savings milestone")
        sub_title.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 500;")
        header_layout.addWidget(sub_title)
        layout.addWidget(header_wrap)

        # Goal selector
        layout.addWidget(QLabel("Target Savings Goal *"))
        self.goal_combo = QComboBox()
        self.goal_combo.setCursor(Qt.PointingHandCursor)
        self.goal_combo.setFixedHeight(38)
        goals = SavingsService.get_all_goals()
        if not goals:
            self.goal_combo.addItem("⚠️ No active goals found (Create a goal first)", None)
        else:
            for g in goals:
                member_tag = f"({g.family_member.name})" if g.family_member else ""
                self.goal_combo.addItem(f"{g.goal_name} {member_tag} - Target: ₹{g.target_amount_paise/100:,.0f}", g.id)
                if preselected_goal_id and g.id == preselected_goal_id:
                    self.goal_combo.setCurrentIndex(self.goal_combo.count() - 1)
        layout.addWidget(self.goal_combo)

        # Deposit Amount
        layout.addWidget(QLabel("Contribution Amount (₹) *"))
        self.amount_input = QLineEdit()
        self.amount_input.setFixedHeight(38)
        self.amount_input.setPlaceholderText("e.g. 5000")
        layout.addWidget(self.amount_input)

        # Source Account
        layout.addWidget(QLabel("Deduct From Account (Optional)"))
        self.account_combo = QComboBox()
        self.account_combo.setCursor(Qt.PointingHandCursor)
        self.account_combo.setFixedHeight(38)
        self.account_combo.addItem("None (External or Cash savings)", None)
        accounts = AccountService.get_all_accounts()
        for a in accounts:
            self.account_combo.addItem(f"{a.name} (Bal: ₹{a.current_balance_paise/100:,.2f})", a.id)
        layout.addWidget(self.account_combo)

        # Date
        layout.addWidget(QLabel("Contribution Date"))
        self.date_edit = QDateEdit()
        self.date_edit.setFixedHeight(38)
        self.date_edit.setCalendarPopup(True)
        today = date.today()
        self.date_edit.setDate(QDate(today.year, today.month, today.day))
        layout.addWidget(self.date_edit)

        # Notes
        layout.addWidget(QLabel("Notes / Reference"))
        self.notes_input = QLineEdit()
        self.notes_input.setFixedHeight(38)
        self.notes_input.setPlaceholderText("e.g. Salary bonus deposit")
        layout.addWidget(self.notes_input)

        layout.addSpacing(6)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b; color: #94a3b8;
                border: 1px solid #334155; padding: 8px 18px; border-radius: 8px; font-weight: 600;
            }
            QPushButton:hover { background-color: #334155; color: #f8fafc; }
        """)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Record Deposit")
        save_btn.setFixedHeight(40)
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
                color: white; font-weight: 700; padding: 8px 22px; border-radius: 8px; border: 1px solid #34d399;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #34d399);
                color: #0f172a;
            }
        """)
        save_btn.clicked.connect(self.save)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def save(self):
        goal_id = self.goal_combo.currentData()
        if not goal_id:
            QMessageBox.warning(self, "Validation Error", "Please select an active savings goal. If none exist, create one first.")
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
