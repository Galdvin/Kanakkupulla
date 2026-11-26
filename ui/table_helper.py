"""
Fintech Table Styling & Column Layout Helper
Provides consistent, modern column sizing, row padding, and header clarity across all tables in Kanakkupulla.
"""
from typing import Optional, Dict
from PySide6.QtWidgets import QTableWidget, QHeaderView
from PySide6.QtCore import Qt


# Standard Column Width Presets for all application views
EXPENSES_DAILY_WIDTHS = {
    0: 55,   # ID
    1: 100,  # Date
    2: 180,  # Title (Stretch)
    3: 140,  # Category
    4: 130,  # Paid By
    5: 130,  # Expense For
    6: 170,  # Account / Mode
    7: 100,  # Attachments
    8: 125,  # Amount
}

EXPENSES_OCCASIONAL_WIDTHS = {
    0: 55,   # ID
    1: 100,  # Date
    2: 180,  # Title (Stretch)
    3: 150,  # Event / Occasion
    4: 135,  # Category
    5: 125,  # Paid By
    6: 125,  # Expense For
    7: 165,  # Account / Mode
    8: 100,  # Attachments
    9: 125,  # Amount
}

INCOME_WIDTHS = {
    0: 55,   # ID
    1: 100,  # Date
    2: 180,  # Source / Title (Stretch)
    3: 130,  # Received By
    4: 160,  # Credited Account
    5: 130,  # Payment Mode
    6: 120,  # Ref No
    7: 125,  # Amount
}

ACCOUNTS_WIDTHS = {
    0: 55,   # ID
    1: 190,  # Account Name (Stretch)
    2: 140,  # Account Type
    3: 160,  # Institution
    4: 135,  # Opening Balance
    5: 145,  # Current Balance
}

LEDGER_WIDTHS = {
    0: 70,   # Entry ID
    1: 70,   # Txn ID
    2: 100,  # Date
    3: 160,  # Account
    4: 200,  # Description (Stretch)
    5: 125,  # Debit (₹)
    6: 125,  # Credit (₹)
}

SUBSCRIPTION_WIDTHS = {
    0: 180,  # Subscription (Stretch)
    1: 110,  # Frequency
    2: 120,  # Billed Amount
    3: 120,  # Monthly Cost
    4: 120,  # Annual Cost
    5: 115,  # Next Renewal
    6: 95,   # Status
}

INVESTMENTS_WIDTHS = {
    0: 180,  # Asset Name (Stretch)
    1: 110,  # Type
    2: 110,  # Units / Quantity
    3: 120,  # Avg Buy Price
    4: 120,  # Current Price
    5: 130,  # Invested Amount
    6: 130,  # Current Value
    7: 130,  # Unrealized P&L
}

RECURRING_WIDTHS = {
    0: 180,  # Rule Name (Stretch)
    1: 95,   # Type
    2: 105,  # Frequency
    3: 115,  # Next Due Date
    4: 125,  # Amount (₹)
    5: 135,  # Category
    6: 145,  # Account
    7: 95,   # Status
}

PLANNING_WIDTHS = {
    0: 110,  # Month
    1: 125,  # Projected Inflow
    2: 125,  # Fixed Obligations
    3: 125,  # Variable Expenses
    4: 125,  # Total Outflow
    5: 140,  # Net Surplus / Savings
    6: 155,  # Projected Bank Balance
    7: 105,  # Savings Rate
}

USERS_WIDTHS = {
    0: 55,   # ID
    1: 180,  # Name (Stretch)
    2: 130,  # Username
    3: 110,  # Role
    4: 100,  # Status
    5: 115,  # Date Added
}

BACKUP_WIDTHS = {
    0: 240,  # Filename (Stretch)
    1: 165,  # Created At
    2: 100,  # Size
    3: 110,  # Type
}

BUDGET_CATEGORY_WIDTHS = {
    0: 220,  # Category (Stretch)
    1: 140,  # Allocated (₹)
}

REPORTS_CAT_WIDTHS = {
    0: 180,  # Category (Stretch)
    1: 85,   # Count
    2: 125,  # Total (₹)
    3: 85,   # Share
}

REPORTS_MEMBER_WIDTHS = {
    0: 160,  # Member (Stretch)
    1: 110,  # Role
    2: 125,  # Paid (₹)
    3: 125,  # Benefited (₹)
    4: 125,  # Net (₹)
}


def configure_fintech_table(
    table: QTableWidget,
    stretch_col: Optional[int] = None,
    col_widths: Optional[Dict[int, int]] = None,
    min_col_width: int = 65,
    row_height: int = 38,
    header_height: int = 40,
    alternating_rows: bool = True
) -> None:
    """
    Standardizes table layout and typography across Kanakkupulla:
    - Eliminates cramped, truncated column headers.
    - Enables interactive user dragging so users can resize columns on the fly.
    - Sets minimum column sizes to prevent title merging.
    - Sets generous default column widths.
    - Allows designated columns (e.g., Title/Description) to stretch flexibly.
    - Sets modern 38-40px row heights.
    """
    table.setAlternatingRowColors(alternating_rows)
    table.setShowGrid(True)
    table.setWordWrap(False)
    
    # Configure vertical header (row heights)
    v_header = table.verticalHeader()
    v_header.setVisible(False)
    v_header.setDefaultSectionSize(row_height)
    
    # Configure horizontal header
    h_header = table.horizontalHeader()
    h_header.setHighlightSections(False)
    h_header.setMinimumSectionSize(min_col_width)
    h_header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    h_header.setFixedHeight(header_height)
    
    col_count = table.columnCount()
    
    # By default, make all columns Interactive so users can drag-resize them
    for col in range(col_count):
        h_header.setSectionResizeMode(col, QHeaderView.Interactive)
    
    # Apply custom column widths if provided
    if col_widths:
        for col, width in col_widths.items():
            if col < col_count:
                table.setColumnWidth(col, width)
                
    # If a stretch column is specified, make it stretch to fill remaining room
    if stretch_col is not None and stretch_col < col_count:
        h_header.setSectionResizeMode(stretch_col, QHeaderView.Stretch)
