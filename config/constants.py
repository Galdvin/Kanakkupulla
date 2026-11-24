"""
Application Constants and Enums
"""
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    STANDARD = "standard"
    VIEWER = "viewer"

class AccountType(str, Enum):
    CASH = "Cash"
    SAVINGS = "Savings Bank Account"
    CURRENT = "Current Account"
    UPI = "UPI Wallet"
    DIGITAL_WALLET = "Digital Wallet"
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    FIXED_DEPOSIT = "Fixed Deposit"
    OTHER = "Other"

class TransactionType(str, Enum):
    EXPENSE = "Expense"
    INCOME = "Income"
    TRANSFER = "Transfer"
    CREDIT_PAYMENT = "Credit Card Payment"

class ExpenseKind(str, Enum):
    DAILY = "Daily"
    OCCASIONAL = "Occasional / Other"

class RecurringFrequency(str, Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    HALF_YEARLY = "Half-Yearly"
    YEARLY = "Yearly"

class LoanStatus(str, Enum):
    ACTIVE = "Active"
    CLOSED = "Closed"
    DEFAULTED = "Defaulted"

class GoalPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

# Default Categories and Subcategories
DEFAULT_CATEGORIES = {
    "Food & Dining": ["Tea / Coffee", "Breakfast", "Lunch", "Dinner", "Snacks", "Restaurant", "Food Delivery"],
    "Groceries": ["Vegetables", "Fruits", "Dairy & Milk", "Rice & Grains", "Provisions", "Spices", "Toiletries"],
    "Transportation": ["Bus / Train", "Auto / Taxi", "Metro", "Flight", "Toll & Parking"],
    "Fuel": ["Petrol", "Diesel", "CNG", "EV Charging"],
    "Housing": ["Rent", "Society Maintenance", "Property Tax", "Water Charges"],
    "Electricity & Utilities": ["Electricity Bill", "Piped Gas / LPG", "Internet / Broadband", "Mobile Recharge", "Cable / DTH"],
    "Medical & Healthcare": ["Doctor Consultation", "Medicines", "Lab Tests", "Hospitalization", "Health Insurance"],
    "Education": ["School Fees", "College Fees", "Tuition & Coaching", "Books & Stationery", "Uniform"],
    "Children's Expenses": ["Toys", "Activities", "Pocket Money", "Baby Care", "Snacks"],
    "Shopping": ["Online Shopping", "Electronics", "Home Appliances", "Books", "Gifts"],
    "Clothing": ["Men's Wear", "Women's Wear", "Kids' Clothing", "Footwear", "Tailoring"],
    "Entertainment": ["Movies", "OTT Subscriptions", "Outing", "Gaming", "Hobbies"],
    "Travel & Vacation": ["Hotel / Resort", "Sightseeing", "Tour Packages", "Travel Tickets"],
    "Family & Functions": ["Diwali", "Pongal", "Birthdays", "Weddings", "Family Get-together", "Gifts"],
    "Insurance": ["Life Insurance (Term)", "Vehicle Insurance", "Health Insurance", "Home Insurance"],
    "Loan & EMI": ["Home Loan EMI", "Car Loan EMI", "Personal Loan EMI", "Gold Loan Interest", "Education Loan EMI"],
    "Investments": ["Mutual Funds (SIP)", "Stocks", "Fixed Deposit", "PPF / EPF", "NPS", "Gold / Sovereign Gold Bonds"],
    "Savings": ["Emergency Fund", "Recurring Deposit", "General Savings", "Goal Savings"],
    "Bank Charges": ["ATM Charges", "Account Maintenance", "Card Annual Fee", "Interest Charges", "Penalties"],
    "Personal Care": ["Haircut & Salon", "Cosmetics", "Gym & Fitness", "Spa"],
    "Donations": ["Temple / Religious", "Charity", "Helping Others"],
    "Vehicle Maintenance": ["Vehicle Service", "Repairs & Spares", "Washing & Polishing", "Insurance Renewal"],
    "Home Maintenance": ["Plumbing", "Electrical", "Carpentry", "Painting", "Appliance Repair"],
    "Subscriptions": ["Software / Apps", "Newspaper / Magazines", "Streaming Services", "Memberships"],
    "Taxes": ["Income Tax", "Advance Tax", "GST", "Professional Tax"],
    "Miscellaneous": ["Uncategorized", "Emergency Cash", "Other Expenses"]
}

DEFAULT_INCOME_SOURCES = [
    "Monthly Salary",
    "Business Income",
    "Freelancing",
    "Rental Income",
    "Bank Interest",
    "Fixed Deposit Interest",
    "Dividend Income",
    "Investment Returns",
    "Pension",
    "Bonus",
    "Incentives",
    "Gift Received",
    "Other Income"
]
