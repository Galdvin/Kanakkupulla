"""
Premium Fintech Dark Theme for Kanakkupulla:
Palette:
- Main Background: Obsidian Black & Midnight Blue (#090d16 to #0d1322)
- Sidebar / Surfaces: Dark Obsidian (#0b0f19)
- Cards & Modals: Glassmorphic Slate Charcoal with ambient borders (#111a2e to #0b1120)
- Borders: Subtle Slate Glass (rgba(255, 255, 255, 0.08) / #1e293b)
- Primary Accent: Deep Teal (#0d9488) / Radiant Teal (#14b8a6)
- Income / Positive: Emerald Green (#10b981)
- Expenses / Negative: Rose / Crimson (#f43f5e)
- Warning / Attention: Amber (#f59e0b)
- Info / Balance: Sky Blue (#38bdf8)
- Typography: Segoe UI / Inter (Rounded 8px-12px)
"""

FINTECH_DARK_THEME = """
/* Kanakkupulla Premium Fintech Glassmorphic Dark Theme */
QWidget {
    background-color: #090d16;
    color: #f8fafc;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

QToolTip {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}

QMainWindow, QDialog {
    background-color: #090d16;
}

/* Sidebar navigation */
QFrame#Sidebar {
    background-color: #0b0f19;
    border-right: 1px solid #1e293b;
}

QScrollArea#NavScrollArea {
    background-color: transparent;
    border: none;
}

QWidget#NavScrollContent {
    background-color: transparent;
}

QLabel#LogoText {
    font-size: 18px;
    font-weight: 800;
    color: #14b8a6;
    letter-spacing: 0.5px;
}

QLabel.NavSectionHeader, QLabel[class="NavSectionHeader"] {
    color: #475569;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 10px 4px 4px 8px;
    text-transform: uppercase;
}

QPushButton.NavBtn, QPushButton[class="NavBtn"] {
    background-color: transparent;
    color: #94a3b8;
    text-align: left;
    padding: 6px 14px;
    min-height: 24px;
    height: 36px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    border: none;
    margin: 1px 2px;
}

QPushButton.NavBtn:hover, QPushButton[class="NavBtn"]:hover {
    background-color: rgba(30, 41, 59, 0.7);
    color: #ffffff;
}

QPushButton.NavBtn:checked, QPushButton[class="NavBtn"]:checked, QPushButton.NavBtn[active="true"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(20, 184, 166, 0.22), stop:1 rgba(15, 23, 42, 0.35));
    color: #2dd4bf;
    font-weight: 700;
    border-left: 3px solid #14b8a6;
}

/* Cards & KPI Containers */
QFrame.Card, QFrame[class="Card"] {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #111a2e, stop:1 #0b1120);
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 16px;
}

QFrame.Card:hover, QFrame[class="Card"]:hover {
    border-color: #334155;
}

QLabel.CardTitle, QLabel[class="CardTitle"] {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel.CardValue, QLabel[class="CardValue"] {
    font-size: 22px;
    font-weight: 800;
    color: #f8fafc;
}

/* Form inputs */
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    background-color: #0b1120;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 7px 12px;
    min-height: 26px;
    font-size: 13px;
    selection-background-color: #0d9488;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #14b8a6;
    background-color: #090d16;
}

QComboBox {
    padding: 7px 12px;
    min-height: 26px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid #1e293b;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}

QComboBox::down-arrow {
    image: url("assets/icons/chevron_down.svg");
    width: 10px;
    height: 10px;
}

QComboBox QAbstractItemView {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 8px;
    selection-background-color: rgba(20, 184, 166, 0.22);
    selection-color: #2dd4bf;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    min-height: 30px;
    padding: 6px 10px;
    color: #f8fafc;
    background-color: #0f172a;
    border-radius: 6px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #1e293b;
    color: #ffffff;
}

QComboBox QAbstractItemView::item:selected {
    background-color: rgba(20, 184, 166, 0.22);
    color: #2dd4bf;
    font-weight: 600;
}

/* Tables & Table Headers (Fintech Luxury Design) */
QTableWidget, QTableView {
    background-color: #090e1a;
    alternate-background-color: #0e1526;
    border: 1px solid #1e293b;
    border-radius: 10px;
    gridline-color: rgba(30, 41, 59, 0.7);
    selection-background-color: rgba(20, 184, 166, 0.22);
    selection-color: #ffffff;
    outline: none;
}

QTableWidget::item, QTableView::item {
    padding: 8px 14px;
    border-bottom: 1px solid rgba(30, 41, 59, 0.6);
    color: #e2e8f0;
    font-size: 13px;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: rgba(20, 184, 166, 0.25);
    color: #2dd4bf;
    font-weight: 600;
}

QTableWidget::item:hover, QTableView::item:hover {
    background-color: rgba(30, 41, 59, 0.65);
}

QHeaderView {
    background-color: #0c1424;
    border: none;
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
}

QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #1b2840, 
        stop:0.45 #121c2e, 
        stop:1 #0b1322);
    color: #93c5fd;
    padding: 10px 14px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.8px;
    border: none;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    border-bottom: 2px solid #14b8a6;
    text-transform: uppercase;
}

QHeaderView::section:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #233656, 
        stop:0.45 #19273f, 
        stop:1 #101c30);
    color: #38bdf8;
    border-bottom: 2px solid #2dd4bf;
}

QHeaderView::section:first {
    border-top-left-radius: 9px;
}

QHeaderView::section:last {
    border-right: none;
    border-top-right-radius: 9px;
}

QTableCornerButton::section {
    background: #121c2e;
    border: none;
    border-bottom: 2px solid #14b8a6;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

/* Buttons */
QPushButton {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #475569;
}

QPushButton.PrimaryBtn, QPushButton[class="PrimaryBtn"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0d9488, stop:1 #14b8a6);
    color: #ffffff;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
}

QPushButton.PrimaryBtn:hover, QPushButton[class="PrimaryBtn"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f766e, stop:1 #0d9488);
}

QPushButton.SuccessBtn, QPushButton[class="SuccessBtn"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
    color: #ffffff;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
}

QPushButton.SuccessBtn:hover, QPushButton[class="SuccessBtn"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
}

QPushButton.DangerBtn, QPushButton[class="DangerBtn"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e11d48, stop:1 #f43f5e);
    color: #ffffff;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
}

QPushButton.DangerBtn:hover, QPushButton[class="DangerBtn"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #be123c, stop:1 #e11d48);
}

/* Scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 25px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #14b8a6;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
    border: none;
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    margin: 0px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #334155;
    min-width: 25px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal:hover {
    background: #14b8a6;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
    border: none;
    width: 0px;
}

/* Tab Widgets */
QTabWidget::pane {
    border: 1px solid #1e293b;
    background-color: #0f172a;
    border-radius: 10px;
}

QTabBar::tab {
    background-color: #0b1120;
    color: #94a3b8;
    padding: 8px 16px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #0f172a;
    color: #14b8a6;
    border-bottom: 2px solid #14b8a6;
}

QTabBar::tab:hover:not(:selected) {
    background-color: #1e293b;
    color: #ffffff;
}
"""
