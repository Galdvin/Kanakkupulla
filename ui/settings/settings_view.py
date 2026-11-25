"""
Settings & Disaster Recovery View:
Comprehensive administration interface for:
1. General currency and date preferences
2. Complete backup (.kpk) creation & restore
3. Family profile naming
4. System environment diagnostics and storage statistics
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QFrame, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from core.settings_service import SettingsService
from core.backup_service import BackupService

class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)

        # Header Bar
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("System Settings & Data Recovery")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #f8fafc;")
        sub_lbl = QLabel("Manage preferences, create timestamped package backups, restore data, and view diagnostics.")
        sub_lbl.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header.addLayout(title_box)
        header.addStretch()
        self.layout.addLayout(header)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #334155; background-color: #1e293b; border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #0f172a; color: #94a3b8; padding: 10px 20px;
                border: 1px solid #334155; border-bottom: none; border-top-left-radius: 6px;
                border-top-right-radius: 6px; font-size: 13px; font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: #1e293b; color: #38bdf8; border-color: #38bdf8;
            }
        """)

        # Add Tabs
        self.init_general_tab()
        self.init_backup_tab()
        self.init_family_tab()
        self.init_about_tab()

        self.layout.addWidget(self.tabs)

    def init_general_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        # Currency
        row1 = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Currency Symbol:"))
        self.currency_sym_input = QLineEdit()
        self.currency_sym_input.setStyleSheet("background-color: #0f172a; color: #f8fafc; padding: 8px; border-radius: 6px; border: 1px solid #334155;")
        v1.addWidget(self.currency_sym_input)
        row1.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Currency Code:"))
        self.currency_code_input = QLineEdit()
        self.currency_code_input.setStyleSheet("background-color: #0f172a; color: #f8fafc; padding: 8px; border-radius: 6px; border: 1px solid #334155;")
        v2.addWidget(self.currency_code_input)
        row1.addLayout(v2)
        lay.addLayout(row1)

        # Date Format & Fiscal Year
        row2 = QHBoxLayout()
        v3 = QVBoxLayout()
        v3.addWidget(QLabel("Date Display Format:"))
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems(["DD-MM-YYYY (%d-%m-%Y)", "YYYY-MM-DD (%Y-%m-%d)", "MM-DD-YYYY (%m-%d-%Y)"])
        self.date_format_combo.setStyleSheet("background-color: #0f172a; color: #f8fafc; padding: 8px; border-radius: 6px; border: 1px solid #334155;")
        v3.addWidget(self.date_format_combo)
        row2.addLayout(v3)

        v4 = QVBoxLayout()
        v4.addWidget(QLabel("Fiscal Year Starts In:"))
        self.fiscal_combo = QComboBox()
        self.fiscal_combo.addItems(["April (Indian Standard)", "January (Calendar Year)"])
        self.fiscal_combo.setStyleSheet("background-color: #0f172a; color: #f8fafc; padding: 8px; border-radius: 6px; border: 1px solid #334155;")
        v4.addWidget(self.fiscal_combo)
        row2.addLayout(v4)
        lay.addLayout(row2)

        # Save Button
        save_btn = QPushButton("Save Preferences")
        save_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: 700; padding: 10px 24px; border-radius: 6px; max-width: 180px;")
        save_btn.clicked.connect(self.save_general_settings)
        lay.addWidget(save_btn)
        lay.addStretch()

        self.tabs.addTab(tab, "⚙ General Preferences")
        self.load_general_settings()

    def init_backup_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        # Actions Row
        act_row = QHBoxLayout()
        backup_btn = QPushButton("📦 Create Complete Package Backup (.kpk)")
        backup_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: 700; padding: 10px 18px; border-radius: 6px;")
        backup_btn.clicked.connect(self.create_backup)
        act_row.addWidget(backup_btn)

        restore_btn = QPushButton("🔄 Restore from Backup File")
        restore_btn.setStyleSheet("background-color: #f43f5e; color: white; font-weight: 700; padding: 10px 18px; border-radius: 6px;")
        restore_btn.clicked.connect(self.restore_backup)
        act_row.addWidget(restore_btn)

        act_row.addStretch()

        refresh_btn = QPushButton("↻ Refresh List")
        refresh_btn.setStyleSheet("background-color: #334155; color: #f8fafc; padding: 10px 16px; border-radius: 6px;")
        refresh_btn.clicked.connect(self.load_backups_list)
        act_row.addWidget(refresh_btn)
        lay.addLayout(act_row)

        # Backups Table
        t_lbl = QLabel("Existing Backups & Archives:")
        t_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #cbd5e1;")
        lay.addWidget(t_lbl)

        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels(["Filename", "Created At", "Size", "Type"])
        self.backup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 4):
            self.backup_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.backup_table.setStyleSheet("background-color: #0f172a; border: 1px solid #334155; gridline-color: #334155; color: #f8fafc; border-radius: 6px;")
        lay.addWidget(self.backup_table)

        self.tabs.addTab(tab, "💾 Backup & Recovery")
        self.load_backups_list()

    def init_family_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        prof = SettingsService.get_family_profile()

        lay.addWidget(QLabel("Household / Family Name:"))
        self.family_name_input = QLineEdit(prof["family_name"])
        self.family_name_input.setStyleSheet("background-color: #0f172a; color: #f8fafc; padding: 8px 12px; border-radius: 6px; border: 1px solid #334155; max-width: 320px;")
        lay.addWidget(self.family_name_input)

        update_btn = QPushButton("Update Family Name")
        update_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: 600; padding: 8px 18px; border-radius: 6px; max-width: 180px;")
        update_btn.clicked.connect(self.save_family_name)
        lay.addWidget(update_btn)

        lay.addSpacing(15)

        # Summary box
        stat_frame = QFrame()
        stat_frame.setStyleSheet("background-color: #0f172a; border-radius: 8px; padding: 16px; border: 1px solid #334155; max-width: 480px;")
        s_lay = QVBoxLayout(stat_frame)
        s_lay.setSpacing(8)
        s_lay.addWidget(QLabel(f"● Total User Profiles: {prof['user_count']}"))
        s_lay.addWidget(QLabel(f"● Total Active Transactions: {prof['transaction_count']}"))
        s_lay.addWidget(QLabel("● Security Model: Argon2id Password Hashing (Salted)"))
        lay.addWidget(stat_frame)

        lay.addStretch()
        self.tabs.addTab(tab, "👨‍👩‍👧‍👦 Family Profile")

    def init_about_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)

        diag = SettingsService.get_system_diagnostics()

        app_title = QLabel(f"{diag['app_name']} Desktop — Personal & Family Finance")
        app_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #38bdf8;")
        lay.addWidget(app_title)

        off_lbl = QLabel(f"🔒 {diag['offline_status']}")
        off_lbl.setStyleSheet("color: #10b981; font-weight: 600; font-size: 13px;")
        lay.addWidget(off_lbl)

        lay.addSpacing(10)

        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #0f172a; border-radius: 8px; padding: 18px; border: 1px solid #334155;")
        i_lay = QVBoxLayout(info_frame)
        i_lay.setSpacing(8)

        i_lay.addWidget(QLabel(f"<b>Application Version:</b> {diag['app_version']}"))
        i_lay.addWidget(QLabel(f"<b>Operating System:</b> {diag['os_version']}"))
        i_lay.addWidget(QLabel(f"<b>Python Runtime:</b> Python {diag['python_version']}"))
        i_lay.addWidget(QLabel(f"<b>GUI Framework:</b> PySide6 {diag['pyside6_version']} (Qt 6)"))
        i_lay.addWidget(QLabel(f"<b>Database Engine:</b> SQLite {diag['sqlite_version']} (WAL Mode, Foreign Keys)"))
        i_lay.addWidget(QLabel(f"<b>ORM:</b> SQLAlchemy {diag['sqlalchemy_version']}"))
        i_lay.addWidget(QLabel(f"<b>Database Location:</b> {diag['db_path']} ({diag['db_size_mb']} MB)"))
        i_lay.addWidget(QLabel(f"<b>Attachments Storage:</b> {diag['attachment_count']} files ({diag['attachment_size_mb']} MB)"))
        i_lay.addWidget(QLabel(f"<b>Password Encryption:</b> {diag['argon2_config']}"))

        lay.addWidget(info_frame)
        lay.addStretch()
        self.tabs.addTab(tab, "ℹ Diagnostics & About")

    def load_general_settings(self):
        settings = SettingsService.get_all_settings()
        self.currency_sym_input.setText(settings.get("app_currency_symbol", "₹"))
        self.currency_code_input.setText(settings.get("app_currency_code", "INR"))

    def save_general_settings(self):
        sym = self.currency_sym_input.text().strip() or "₹"
        code = self.currency_code_input.text().strip() or "INR"
        SettingsService.set_setting("app_currency_symbol", sym)
        SettingsService.set_setting("app_currency_code", code)
        QMessageBox.information(self, "Settings Saved", "Preferences updated successfully!")

    def save_family_name(self):
        name = self.family_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Family name cannot be empty.")
            return
        if SettingsService.update_family_name(name):
            QMessageBox.information(self, "Success", "Family profile name updated successfully!")
        else:
            QMessageBox.critical(self, "Error", "Could not update family name.")

    def load_backups_list(self):
        backups = BackupService.list_backups()
        self.backup_table.setRowCount(len(backups))
        for row, b in enumerate(backups):
            self.backup_table.setItem(row, 0, QTableWidgetItem(b["filename"]))
            self.backup_table.setItem(row, 1, QTableWidgetItem(b["created_at"].strftime("%d-%m-%Y %H:%M:%S")))
            self.backup_table.setItem(row, 2, QTableWidgetItem(f"{b['size_mb']} MB"))
            pkg_type = "Full Package (.kpk)" if b["is_package"] else "Database Only (.db)"
            self.backup_table.setItem(row, 3, QTableWidgetItem(pkg_type))

    def create_backup(self):
        ok, msg, path = BackupService.create_backup()
        if ok:
            QMessageBox.information(self, "Backup Successful", f"Full backup archive generated:\n{path.name}")
            self.load_backups_list()
        else:
            QMessageBox.critical(self, "Backup Failed", msg)

    def restore_backup(self):
        file_path_str, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File to Restore", "",
            "Kanakkupulla Backups (*.kpk *.zip *.db)"
        )
        if not file_path_str:
            return

        reply = QMessageBox.warning(
            self, "Confirm Restore",
            "Restoring a backup will replace your current active database with the backup archive.\n\n"
            "A safety snapshot of your current database will be automatically created before restoring.\n\n"
            "Do you wish to proceed?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            ok, msg = BackupService.restore_backup(Path(file_path_str))
            if ok:
                QMessageBox.information(
                    self, "Restore Successful",
                    f"{msg}\n\nPlease restart Kanakkupulla to ensure all active connections reload."
                )
                self.load_backups_list()
            else:
                QMessageBox.critical(self, "Restore Failed", msg)
