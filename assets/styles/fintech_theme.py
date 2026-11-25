"""
Premium Fintech Dark Theme for Kanakkupulla:
Palette:
- Main Background: Deep Navy (#0a0f1d)
- Sidebar / Surfaces: Dark Charcoal (#111827)
- Cards & Modals: Slate Charcoal (#1e293b)
- Borders: Subtle Slate (#334155)
- Primary Accent: Deep Teal (#0d9488) / Vibrant Teal (#14b8a6)
- Income / Positive: Emerald Green (#10b981)
- Expenses / Negative: Crimson Red (#ef4444)
- Warning / Attention: Amber (#f59e0b)
- Typography: Segoe UI / Inter (Rounded 10px-14px)
"""

FINTECH_DARK_THEME = """
/* Kanakkupulla Premium Fintech Dark Theme */
QWidget {
    background-color: #0a0f1d;
    color: #f8fafc;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

QToolTip {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 12px;
}

QMainWindow, QDialog {
    background-color: #0a0f1d;
}

/* Sidebar navigation */
QFrame#Sidebar {
    background-color: #0d1322;
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
    background-color: #1e293b;
    color: #ffffff;
}

QPushButton.NavBtn:checked, QPushButton[class="NavBtn"]:checked, QPushButton.NavBtn[active="true"] {
    background-color: #0d9488;
    color: #ffffff;
    font-weight: 600;
}

/* Cards & KPI Containers */
QFrame.Card {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px;
}

QLabel.CardTitle {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel.CardValue {
    font-size: 24px;
    font-weight: 800;
    color: #f8fafc;
}

/* Form inputs */
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    background-color: #111827;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    selection-background-color: #0d9488;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
    border: 1px solid #14b8a6;
    background-color: #0a0f1d;
}

/* Tables */
QTableWidget, QTableView {
    background-color: #111827;
    border: 1px solid #334155;
    border-radius: 10px;
    gridline-color: #1f2937;
    selection-background-color: #0f766e;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #0a0f1d;
    color: #94a3b8;
    padding: 10px;
    font-weight: 700;
    border: none;
    border-bottom: 2px solid #334155;
}

/* Buttons */
QPushButton.PrimaryBtn {
    background-color: #0d9488;
    color: #ffffff;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
}

QPushButton.PrimaryBtn:hover {
    background-color: #0f766e;
}

QPushButton.SuccessBtn {
    background-color: #10b981;
    color: #ffffff;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
}

QPushButton.SuccessBtn:hover {
    background-color: #059669;
}

QPushButton.DangerBtn {
    background-color: #ef4444;
    color: #ffffff;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
}

QPushButton.DangerBtn:hover {
    background-color: #dc2626;
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
"""
