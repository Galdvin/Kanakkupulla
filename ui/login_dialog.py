"""
Modern Graphical Fintech Login Dialog for Kanakkupulla
Features:
- Dual-panel hero glassmorphism layout (Branding & Feature Showcase on left, Auth Form on right)
- SVG App Logo with glowing aura
- Password visibility toggle (Eye icon)
- One-click demo credential autofill pill (admin / admin123)
- Argon2id cryptographic vault status beacon
- Keyboard Enter triggers instant login
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap
from core.authentication import AuthService
from config.settings import ASSETS_DIR

APP_LOGO_PATH = ASSETS_DIR / "icons" / "app_logo.svg"


class LoginDialog(QDialog):
    login_success = Signal(object) # Emits authenticated user

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kanakkupulla - Sign In")
        self.setFixedSize(820, 510)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #090d16;
            }
        """)
        self.init_ui()

    def init_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ========================================================
        # LEFT HERO PANEL (Visual Branding & Graphical Highlights)
        # ========================================================
        hero_panel = QFrame()
        hero_panel.setObjectName("HeroPanel")
        hero_panel.setStyleSheet("""
            QFrame#HeroPanel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #0f1c33, 
                    stop:0.45 #0b1424, 
                    stop:1 #071f28);
                border-right: 1px solid #1e293b;
            }
        """)
        hero_layout = QVBoxLayout(hero_panel)
        hero_layout.setContentsMargins(36, 40, 36, 36)
        hero_layout.setSpacing(18)

        # App Logo & Brand Header
        brand_row = QHBoxLayout()
        brand_row.setSpacing(12)

        logo_lbl = QLabel()
        if APP_LOGO_PATH.exists():
            pix = QPixmap(str(APP_LOGO_PATH)).scaled(46, 46, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
        else:
            logo_lbl.setText("🪙")
            logo_lbl.setStyleSheet("font-size: 32px;")
        brand_row.addWidget(logo_lbl)

        brand_text_box = QVBoxLayout()
        brand_text_box.setSpacing(2)
        app_title = QLabel("Kanakkupulla")
        app_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #2dd4bf; letter-spacing: -0.5px;")
        app_tamil = QLabel("கணக்குப்புள்ள • Family Finance")
        app_tamil.setStyleSheet("font-size: 11px; font-weight: 500; color: #94a3b8;")
        brand_text_box.addWidget(app_title)
        brand_text_box.addWidget(app_tamil)
        brand_row.addLayout(brand_text_box)
        brand_row.addStretch()
        hero_layout.addLayout(brand_row)

        hero_layout.addSpacing(6)

        # Tagline
        tagline = QLabel("Personal & Family\nFinancial Intelligence")
        tagline.setStyleSheet("font-size: 20px; font-weight: 700; color: #f8fafc; line-height: 1.3;")
        hero_layout.addWidget(tagline)

        tagline_sub = QLabel("Autonomous offline wealth tracking, double-entry bookkeeping, and predictive forecasting for modern families.")
        tagline_sub.setWordWrap(True)
        tagline_sub.setStyleSheet("font-size: 12px; color: #94a3b8; line-height: 1.4;")
        hero_layout.addWidget(tagline_sub)

        hero_layout.addSpacing(6)

        # Feature highlights pills
        features = [
            ("🛡", "100% Offline Vault", "Zero cloud leaks, local SQLite WAL engine"),
            ("📊", "Multi-Axis Cash Flow", "Interactive Recharts-style curves & pacing"),
            ("👨‍👩‍👧‍👦", "Family Attribution", "Consolidated net worth & member splits"),
            ("🎯", "Demand Forecasting", "12-month runway simulation & budget caps"),
        ]

        for icon_str, f_title, f_sub in features:
            f_card = QFrame()
            f_card.setStyleSheet("""
                QFrame {
                    background: rgba(15, 23, 42, 0.55);
                    border: 1px solid rgba(255, 255, 255, 0.06);
                    border-radius: 8px;
                    padding: 4px;
                }
            """)
            f_row = QHBoxLayout(f_card)
            f_row.setContentsMargins(8, 6, 8, 6)
            f_row.setSpacing(10)

            f_icon = QLabel(icon_str)
            f_icon.setStyleSheet("font-size: 14px;")
            f_row.addWidget(f_icon)

            f_text = QVBoxLayout()
            f_text.setSpacing(1)
            f_t = QLabel(f_title)
            f_t.setStyleSheet("font-size: 11px; font-weight: 700; color: #e2e8f0;")
            f_s = QLabel(f_sub)
            f_s.setStyleSheet("font-size: 10px; color: #64748b;")
            f_text.addWidget(f_t)
            f_text.addWidget(f_s)
            f_row.addLayout(f_text)
            f_row.addStretch()

            hero_layout.addWidget(f_card)

        hero_layout.addStretch()

        # Security footer
        sec_lbl = QLabel("🔒 Argon2id Cryptographic Authentication")
        sec_lbl.setStyleSheet("font-size: 10px; color: #10b981; font-weight: 600;")
        hero_layout.addWidget(sec_lbl)

        root_layout.addWidget(hero_panel, stretch=5)

        # ========================================================
        # RIGHT AUTH FORM PANEL (Modern Glassmorphic Sign In)
        # ========================================================
        form_panel = QFrame()
        form_panel.setObjectName("FormPanel")
        form_panel.setStyleSheet("""
            QFrame#FormPanel {
                background-color: #090d16;
            }
        """)
        form_layout = QVBoxLayout(form_panel)
        form_layout.setContentsMargins(42, 40, 42, 36)
        form_layout.setSpacing(14)

        # Form Header
        f_header = QVBoxLayout()
        f_header.setSpacing(4)
        welcome_lbl = QLabel("Welcome Back")
        welcome_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #f8fafc;")
        instruction_lbl = QLabel("Enter your master credentials to unlock the vault")
        instruction_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        f_header.addWidget(welcome_lbl)
        f_header.addWidget(instruction_lbl)
        form_layout.addLayout(f_header)

        form_layout.addSpacing(8)

        # Username Field
        user_box = QVBoxLayout()
        user_box.setSpacing(5)
        u_lbl = QLabel("Username")
        u_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        user_box.addWidget(u_lbl)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("e.g. admin")
        self.user_input.setFixedHeight(42)
        self.user_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 9px;
                padding: 8px 14px;
                color: #f8fafc;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #14b8a6;
                background-color: #0b1120;
            }
        """)
        self.user_input.setText("admin")
        user_box.addWidget(self.user_input)
        form_layout.addLayout(user_box)

        # Password Field with Eye Toggle
        pwd_box = QVBoxLayout()
        pwd_box.setSpacing(5)
        p_lbl = QLabel("Password")
        p_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        pwd_box.addWidget(p_lbl)

        pwd_input_wrap = QHBoxLayout()
        pwd_input_wrap.setSpacing(0)

        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setPlaceholderText("Enter your password")
        self.pwd_input.setFixedHeight(42)
        self.pwd_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-top-left-radius: 9px;
                border-bottom-left-radius: 9px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 8px 14px;
                color: #f8fafc;
                font-size: 13px;
                border-right: none;
            }
            QLineEdit:focus {
                border: 1px solid #14b8a6;
                border-right: none;
                background-color: #0b1120;
            }
        """)
        self.pwd_input.setText("admin123")
        pwd_input_wrap.addWidget(self.pwd_input, stretch=1)

        self.eye_btn = QPushButton("👁")
        self.eye_btn.setFixedSize(42, 42)
        self.eye_btn.setToolTip("Show / Hide password")
        self.eye_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-left: none;
                border-top-right-radius: 9px;
                border-bottom-right-radius: 9px;
                color: #94a3b8;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #2dd4bf;
                background-color: #1e293b;
            }
        """)
        self.eye_btn.clicked.connect(self.toggle_password_visibility)
        pwd_input_wrap.addWidget(self.eye_btn)

        pwd_box.addLayout(pwd_input_wrap)
        form_layout.addLayout(pwd_box)

        # Status / Error Banner
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #f43f5e; font-size: 12px; font-weight: 500;")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setWordWrap(True)
        form_layout.addWidget(self.status_lbl)

        # Sign In Button
        self.login_btn = QPushButton("Unlock Vault  →")
        self.login_btn.setFixedHeight(44)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0d9488, stop:1 #14b8a6);
                color: #ffffff;
                font-size: 14px;
                font-weight: 700;
                border: none;
                border-radius: 9px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f766e, stop:1 #0d9488);
            }
            QPushButton:pressed {
                background: #0f766e;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        self.pwd_input.returnPressed.connect(self.handle_login)
        self.user_input.returnPressed.connect(self.handle_login)
        form_layout.addWidget(self.login_btn)

        # Quick demo fill pill
        self.demo_pill = QPushButton("⚡ Auto-fill credentials: admin / admin123")
        self.demo_pill.setStyleSheet("""
            QPushButton {
                background: rgba(30, 41, 59, 0.5);
                border: 1px dashed #334155;
                color: #94a3b8;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(20, 184, 166, 0.12);
                border-color: #14b8a6;
                color: #2dd4bf;
            }
        """)
        self.demo_pill.clicked.connect(self.autofill_demo)
        form_layout.addWidget(self.demo_pill)

        form_layout.addStretch()

        # Footer version
        ver_lbl = QLabel("Kanakkupulla v1.0.0 • SQLite WAL Offline Security")
        ver_lbl.setAlignment(Qt.AlignCenter)
        ver_lbl.setStyleSheet("font-size: 10px; color: #475569;")
        form_layout.addWidget(ver_lbl)

        root_layout.addWidget(form_panel, stretch=6)

    def toggle_password_visibility(self):
        if self.pwd_input.echoMode() == QLineEdit.Password:
            self.pwd_input.setEchoMode(QLineEdit.Normal)
            self.eye_btn.setText("🔒")
        else:
            self.pwd_input.setEchoMode(QLineEdit.Password)
            self.eye_btn.setText("👁")

    def autofill_demo(self):
        self.user_input.setText("admin")
        self.pwd_input.setText("admin123")
        self.status_lbl.setText("✓ Default credentials applied")
        self.status_lbl.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 500;")

    def handle_login(self):
        username = self.user_input.text().strip()
        password = self.pwd_input.text().strip()

        if not username or not password:
            self.status_lbl.setText("⚠ Please enter both username and password")
            self.status_lbl.setStyleSheet("color: #f43f5e; font-size: 12px; font-weight: 500;")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Verifying Vault Security...")

        ok, msg, user = AuthService.login(username, password)
        if ok:
            self.login_success.emit(user)
            self.accept()
        else:
            self.status_lbl.setText(f"⚠ {msg}")
            self.status_lbl.setStyleSheet("color: #f43f5e; font-size: 12px; font-weight: 500;")
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Unlock Vault  →")
