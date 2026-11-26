"""
Premium Modern Dark & Light Stylesheets for Kanakkupulla Desktop UI
"""

DARK_THEME = """
/* Kanakkupulla Modern Dark Theme */
QWidget {
    background-color: #0f172a;
    color: #f8fafc;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

QMainWindow, QDialog {
    background-color: #0f172a;
}

/* Sidebar navigation */
QFrame#Sidebar {
    background-color: #1e293b;
    border-right: 1px solid #334155;
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
    font-weight: 700;
    color: #38bdf8;
    padding: 2px;
}

QLabel.NavSectionHeader, QLabel[class="NavSectionHeader"] {
    color: #64748b;
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
    background-color: #334155;
    color: #ffffff;
}

QPushButton.NavBtn:checked, QPushButton[class="NavBtn"]:checked, QPushButton.NavBtn[active="true"] {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 600;
}

/* Header & Cards */
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
}

QLabel.CardValue {
    font-size: 22px;
    font-weight: 700;
    color: #f8fafc;
}

/* Forms & Inputs */
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 24px;
    font-size: 13px;
    selection-background-color: #0284c7;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
    border: 1px solid #38bdf8;
    background-color: #0f172a;
}

QComboBox {
    padding: 6px 12px;
    min-height: 24px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid #334155;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #94a3b8;
    width: 0px;
    height: 0px;
}

/* Tables */
QTableWidget, QTableView {
    background-color: #090e1a;
    alternate-background-color: #0e1526;
    border: 1px solid #1e293b;
    border-radius: 10px;
    gridline-color: rgba(30, 41, 59, 0.7);
    selection-background-color: rgba(20, 184, 166, 0.22);
    selection-color: #ffffff;
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

QTableCornerButton::section {
    background: #121c2e;
    border: none;
    border-bottom: 2px solid #14b8a6;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

/* Primary and Action Buttons */
QPushButton.PrimaryBtn {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
}

QPushButton.PrimaryBtn:hover {
    background-color: #0369a1;
}

QPushButton.SuccessBtn {
    background-color: #10b981;
    color: #ffffff;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
}

QPushButton.SuccessBtn:hover {
    background-color: #059669;
}

QPushButton.DangerBtn {
    background-color: #ef4444;
    color: #ffffff;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
}

QPushButton.DangerBtn:hover {
    background-color: #dc2626;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #0f172a;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}
"""

LIGHT_THEME = """
/* Kanakkupulla Clean Modern Light Theme */
QWidget {
    background-color: #f8fafc;
    color: #0f172a;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

QMainWindow, QDialog {
    background-color: #f8fafc;
}

QFrame#Sidebar {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
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
    font-weight: 700;
    color: #0284c7;
    padding: 2px;
}

QLabel.NavSectionHeader, QLabel[class="NavSectionHeader"] {
    color: #94a3b8;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 10px 4px 4px 8px;
    text-transform: uppercase;
}

QPushButton.NavBtn, QPushButton[class="NavBtn"] {
    background-color: transparent;
    color: #64748b;
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
    background-color: #f1f5f9;
    color: #0f172a;
}

QPushButton.NavBtn:checked, QPushButton[class="NavBtn"]:checked, QPushButton.NavBtn[active="true"] {
    background-color: #e0f2fe;
    color: #0284c7;
    font-weight: 600;
}

QFrame.Card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
}

QLabel.CardTitle {
    color: #64748b;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
}

QLabel.CardValue {
    font-size: 22px;
    font-weight: 700;
    color: #0f172a;
}

QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 12px;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
    border: 1px solid #0284c7;
}

QTableWidget, QTableView {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    gridline-color: #f1f5f9;
}

QHeaderView {
    background-color: #f1f5f9;
    border: none;
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
}

QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 #f8fafc, 
        stop:1 #e2e8f0);
    color: #1e293b;
    padding: 10px 14px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.8px;
    border: none;
    border-right: 1px solid #cbd5e1;
    border-bottom: 2px solid #0284c7;
    text-transform: uppercase;
}

QHeaderView::section:hover {
    background: #e2e8f0;
    color: #0284c7;
}

QTableCornerButton::section {
    background: #e2e8f0;
    border: none;
    border-bottom: 2px solid #0284c7;
    border-right: 1px solid #cbd5e1;
}

QPushButton.PrimaryBtn {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
}

QPushButton.PrimaryBtn:hover {
    background-color: #0369a1;
}
"""
