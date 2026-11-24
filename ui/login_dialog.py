"""
Login Dialog for Kanakkupulla
Features secure authentication with username/password, error feedback, and session handling.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from core.authentication import AuthService

class LoginDialog(QDialog):
    login_success = Signal(object) # Emits authenticated user

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kanakkupulla - Sign In")
        self.setFixedSize(420, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 40, 30, 40)
        main_layout.setSpacing(20)

        # Container card
        card = QFrame()
        card.setProperty("class", "Card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)

        # Header Title
        title_label = QLabel("Kanakkupulla")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Segoe UI", 20, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #38bdf8;")

        subtitle_label = QLabel("Personal Finance & Wealth Management")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #94a3b8; font-size: 12px;")

        card_layout.addWidget(title_label)
        card_layout.addWidget(subtitle_label)
        card_layout.addSpacing(15)

        # Username input
        user_lbl = QLabel("Username")
        user_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Enter your username")
        self.user_input.setText("admin") # Pre-filled for convenience in development
        card_layout.addWidget(user_lbl)
        card_layout.addWidget(self.user_input)

        # Password input
        pwd_lbl = QLabel("Password")
        pwd_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setPlaceholderText("Enter password")
        self.pwd_input.setText("admin123")
        card_layout.addWidget(pwd_lbl)
        card_layout.addWidget(self.pwd_input)

        # Status / Error Label
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #ef4444; font-size: 12px;")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.status_lbl)

        # Sign In Button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setProperty("class", "PrimaryBtn")
        self.login_btn.setFixedHeight(40)
        self.login_btn.clicked.connect(self.handle_login)
        self.pwd_input.returnPressed.connect(self.handle_login)
        self.user_input.returnPressed.connect(self.handle_login)
        card_layout.addWidget(self.login_btn)

        # Default info note
        hint_lbl = QLabel("Default: admin / admin123")
        hint_lbl.setAlignment(Qt.AlignCenter)
        hint_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        card_layout.addWidget(hint_lbl)

        main_layout.addWidget(card)

    def handle_login(self):
        username = self.user_input.text().strip()
        password = self.pwd_input.text().strip()

        if not username or not password:
            self.status_lbl.setText("Please enter both username and password")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Authenticating...")

        success, message, user = AuthService.login(username, password)
        if success and user:
            self.login_success.emit(user)
            self.accept()
        else:
            self.status_lbl.setText(message)
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Sign In")
