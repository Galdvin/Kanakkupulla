"""
User Management View & Dialog
Permits viewing, adding, and editing family members / application users with roles.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, 
    QLineEdit, QComboBox, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from core.user_service import UserService
from core.authentication import AuthService
from config.constants import UserRole
from core.financial_utils import format_date
from ui.table_helper import configure_fintech_table, USERS_WIDTHS

class UserEditDialog(QDialog):
    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self.user = user
        self.is_edit = user is not None
        self.setWindowTitle("Edit User" if self.is_edit else "Add New Member / User")
        self.setFixedSize(380, 420)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        # Full Name
        layout.addWidget(QLabel("Full Name / Display Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Arun Kumar, Child 1, Father")
        if self.is_edit:
            self.name_input.setText(self.user.full_name)
        layout.addWidget(self.name_input)

        # Username
        layout.addWidget(QLabel("Username:"))
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Unique login name")
        if self.is_edit:
            self.user_input.setText(self.user.username)
            self.user_input.setEnabled(False) # Username cannot be changed
        layout.addWidget(self.user_input)

        # Password
        layout.addWidget(QLabel("Password" + (" (leave blank to keep unchanged):" if self.is_edit else ":")))
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setPlaceholderText("At least 6 characters")
        layout.addWidget(self.pwd_input)

        # Role
        layout.addWidget(QLabel("Role:"))
        self.role_combo = QComboBox()
        self.role_combo.addItems([UserRole.STANDARD.value, UserRole.ADMIN.value, UserRole.VIEWER.value])
        if self.is_edit:
            self.role_combo.setCurrentText(self.user.role)
        layout.addWidget(self.role_combo)

        # Status
        if self.is_edit:
            layout.addWidget(QLabel("Status:"))
            self.status_combo = QComboBox()
            self.status_combo.addItems(["active", "disabled"])
            self.status_combo.setCurrentText(self.user.status)
            layout.addWidget(self.status_combo)

        # Save Button
        layout.addSpacing(10)
        self.save_btn = QPushButton("Save User")
        self.save_btn.setProperty("class", "PrimaryBtn")
        self.save_btn.clicked.connect(self.save)
        layout.addWidget(self.save_btn)

    def save(self):
        name = self.name_input.text().strip()
        username = self.user_input.text().strip()
        password = self.pwd_input.text().strip()
        role = self.role_combo.currentText()

        if not name:
            QMessageBox.warning(self, "Validation", "Full name is required.")
            return

        if not self.is_edit:
            if not username or not password:
                QMessageBox.warning(self, "Validation", "Username and password are required.")
                return
            success, msg, _ = UserService.create_user(username, name, password, role)
            if success:
                self.accept()
            else:
                QMessageBox.critical(self, "Error", msg)
        else:
            status = self.status_combo.currentText()
            pwd_to_update = password if password else None
            success, msg = UserService.update_user(self.user.id, name, role, status, pwd_to_update)
            if success:
                self.accept()
            else:
                QMessageBox.critical(self, "Error", msg)


class UsersView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header bar
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Family & User Management")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #38bdf8;")
        sub = QLabel("Manage users, family members, roles, and transaction permissions")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.add_btn = QPushButton("+ Add Member / User")
        self.add_btn.setProperty("class", "PrimaryBtn")
        self.add_btn.clicked.connect(self.open_add_dialog)
        header.addWidget(self.add_btn)

        layout.addLayout(header)

        # Users Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Username", "Role", "Status", "Date Added"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.open_edit_dialog)
        configure_fintech_table(self.table, stretch_col=1, col_widths=USERS_WIDTHS)
        layout.addWidget(self.table)

        # Bottom Actions
        actions_bar = QHBoxLayout()
        self.edit_btn = QPushButton("Edit Selected User")
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        actions_bar.addWidget(self.edit_btn)
        actions_bar.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_users)
        actions_bar.addWidget(refresh_btn)

        layout.addLayout(actions_bar)

    def load_users(self):
        users = UserService.get_all_users()
        self.table.setRowCount(len(users))
        for row, u in enumerate(users):
            id_item = QTableWidgetItem(str(u.id))
            id_item.setData(Qt.UserRole, u)
            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, QTableWidgetItem(u.full_name))
            self.table.setItem(row, 2, QTableWidgetItem(u.username))
            self.table.setItem(row, 3, QTableWidgetItem(u.role.capitalize()))
            self.table.setItem(row, 4, QTableWidgetItem(u.status.capitalize()))
            self.table.setItem(row, 5, QTableWidgetItem(format_date(u.created_at.date())))

    def open_add_dialog(self):
        dlg = UserEditDialog(parent=self)
        if dlg.exec():
            self.load_users()

    def open_edit_dialog(self):
        curr_row = self.table.currentRow()
        if curr_row < 0:
            QMessageBox.information(self, "Selection", "Please select a user to edit.")
            return
        user_item = self.table.item(curr_row, 0)
        user = user_item.data(Qt.UserRole)
        dlg = UserEditDialog(user=user, parent=self)
        if dlg.exec():
            self.load_users()
