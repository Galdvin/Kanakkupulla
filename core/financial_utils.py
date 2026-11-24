"""
Financial Utility Functions:
- Indian Currency Formatting (e.g. ₹1,23,456.78)
- Conversion between Integer Paise and INR Float/Decimal
- Date formatting (DD-MM-YYYY)
"""
from typing import Union
from datetime import datetime, date

def paise_to_inr(paise: int) -> float:
    """Converts integer paise to standard float rupees (for display/export)"""
    return (paise or 0) / 100.0

def inr_to_paise(rupees: Union[float, int, str]) -> int:
    """Converts rupees to integer paise without floating point rounding errors"""
    try:
        val = float(rupees)
        return int(round(val * 100))
    except (ValueError, TypeError):
        return 0

def format_inr(paise: int, include_symbol: bool = True) -> str:
    """
    Formats paise into Indian Numbering System:
    e.g. 10000000 paise -> ₹1,00,000.00
    """
    if paise is None:
        paise = 0
        
    is_negative = paise < 0
    abs_paise = abs(paise)
    rupees = abs_paise // 100
    cents = abs_paise % 100

    s = str(rupees)
    if len(s) > 3:
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        formatted_rupees = ",".join(groups) + "," + last3
    else:
        formatted_rupees = s

    res = f"{formatted_rupees}.{cents:02d}"
    if include_symbol:
        res = f"₹{res}"
    if is_negative:
        res = f"-{res}"
    return res

def format_date(dt: Union[date, datetime, str]) -> str:
    """Formats a date object or ISO string to DD-MM-YYYY"""
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt).date()
        except Exception:
            return dt
    return dt.strftime("%d-%m-%Y")

def parse_date(date_str: str) -> date:
    """Parses DD-MM-YYYY or YYYY-MM-DD into a datetime.date object"""
    date_str = date_str.strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Cannot parse date format: {date_str}")
