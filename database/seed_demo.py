"""
Sample Demo Financial Dataset Generator for Kanakkupulla
Creates realistic Indian family financial history:
- Multiple members (Primary Earner, Spouse, Child)
- Bank accounts, Cash, UPI, and Credit Card
- Salaries, Freelance, and Dividend Income
- Daily expenses (Groceries, Fuel, Dining, Utilities)
- Occasional expenses (Diwali Festival, Home Improvement)
- Monthly Budgets
- Savings Goals (Emergency Fund, Child Education)
- Active Investments (Mutual Funds SIP, SGB Gold, Fixed Deposit)
- Home & Vehicle Loans with EMI schedules
"""
from datetime import date, timedelta
from database.connection import SessionLocal
from database.seed import seed_database
from core.authentication import AuthService
from core.user_service import UserService
from core.category_service import CategoryService
from core.accounting_service import AccountService
from core.expense_service import ExpenseService
from core.income_service import IncomeService
from core.budget_service import BudgetService
from core.savings_service import SavingsService
from core.investment_service import InvestmentService
from core.loan_service import LoanService
from config.constants import AccountType, ExpenseKind, UserRole, GoalPriority

def generate_demo_dataset():
    print("Seeding baseline schema...")
    seed_database()

    # Log in as admin
    AuthService.login("admin", "admin123")

    # 1. Users / Family Members
    print("Creating demo family members...")
    _, _, spouse = UserService.create_user("priya", "Priya (Spouse)", "priya123", UserRole.STANDARD.value)
    if not spouse:
        spouse = [u for u in UserService.get_all_users() if u.username == "priya"][0]

    _, _, child = UserService.create_user("aarav", "Aarav (Child)", "aarav123", UserRole.VIEWER.value)
    if not child:
        child = [u for u in UserService.get_all_users() if u.username == "aarav"][0]

    admin = [u for u in UserService.get_all_users() if u.username == "admin"][0]

    # 2. Bank Accounts & Cards
    print("Creating accounts and cards...")
    _, _, hdfc = AccountService.create_account("HDFC Salary Account", AccountType.SAVINGS.value, opening_balance_paise=12500000, institution_name="HDFC Bank") # ₹1,25,000
    _, _, sbi = AccountService.create_account("SBI Joint Savings", AccountType.SAVINGS.value, opening_balance_paise=8000000, institution_name="State Bank of India") # ₹80,000
    _, _, icici_cc = AccountService.create_account("ICICI Coral Credit Card", AccountType.CREDIT_CARD.value, opening_balance_paise=0, credit_limit_paise=25000000, institution_name="ICICI Bank") # ₹2,50,000 limit
    _, _, cash = AccountService.create_account("Home Cash Box", AccountType.CASH.value, opening_balance_paise=1500000) # ₹15,000

    # 3. Monthly Incomes
    print("Generating historical incomes...")
    today = date.today()
    IncomeService.record_income(
        source_title="Monthly Tech Salary",
        amount_paise=14500000, # ₹1,45,000
        income_date=today - timedelta(days=24),
        account_id=hdfc.id,
        received_by_id=admin.id,
        payment_mode="Bank Transfer"
    )
    IncomeService.record_income(
        source_title="Freelance Design Consulting",
        amount_paise=3500000, # ₹35,000
        income_date=today - timedelta(days=12),
        account_id=sbi.id,
        received_by_id=spouse.id,
        payment_mode="UPI"
    )

    # 4. Daily Expenses
    print("Generating daily expense records...")
    categories = {c.name: c.id for c in CategoryService.get_all_categories()}

    demo_expenses = [
        ("Monthly Supermarket Groceries", 1450000, categories.get("Groceries"), hdfc.id, admin.id, admin.id, "Credit Card"), # ₹14,500
        ("Vehicle Petrol Fill", 420000, categories.get("Fuel"), hdfc.id, admin.id, admin.id, "UPI"), # ₹4,200
        ("Vegetables & Fruits (Weekly Market)", 185000, categories.get("Groceries"), cash.id, spouse.id, admin.id, "Cash"), # ₹1,850
        ("Family Weekend Dinner", 360000, categories.get("Food & Dining"), icici_cc.id, admin.id, admin.id, "Credit Card"), # ₹3,600
        ("School Tuition Term Fee", 2200000, categories.get("Education"), hdfc.id, admin.id, child.id, "Net Banking"), # ₹22,000 (Paid By Father, Beneficiary Child)
        ("Electricity & Power Utility Bill", 380000, categories.get("Electricity & Utilities"), hdfc.id, spouse.id, admin.id, "UPI"), # ₹3,800
        ("High-speed Fiber Broadband", 119900, categories.get("Electricity & Utilities"), hdfc.id, admin.id, admin.id, "UPI"), # ₹1,199
        ("Doctor Consultation & Medicines", 215000, categories.get("Medical & Healthcare"), hdfc.id, admin.id, spouse.id, "UPI"), # ₹2,150
        ("Aarav Drawing & Craft Kit", 85000, categories.get("Children's Expenses"), cash.id, spouse.id, child.id, "Cash"), # ₹850
    ]

    for title, amt, cat_id, acc_id, paid_id, for_id, pm in demo_expenses:
        ExpenseService.record_expense(
            title=title,
            amount_paise=amt,
            transaction_date=today - timedelta(days=3),
            account_id=acc_id,
            paid_by_id=paid_id,
            expense_for_id=for_id,
            category_id=cat_id,
            payment_method=pm,
            expense_kind=ExpenseKind.DAILY.value
        )

    # 5. Occasional / Event Expenses
    print("Generating occasional event expenses...")
    ExpenseService.record_expense(
        title="Diwali Sweets & Dry Fruits Gift Hampers",
        amount_paise=650000, # ₹6,500
        transaction_date=today - timedelta(days=15),
        account_id=hdfc.id,
        paid_by_id=admin.id,
        expense_for_id=admin.id,
        category_id=categories.get("Family & Functions"),
        expense_kind=ExpenseKind.OCCASIONAL.value,
        event_name="Diwali 2026 Celebration"
    )
    ExpenseService.record_expense(
        title="Festival Ethnic Traditional Attire",
        amount_paise=1200000, # ₹12,000
        transaction_date=today - timedelta(days=16),
        account_id=icici_cc.id,
        paid_by_id=admin.id,
        expense_for_id=spouse.id,
        category_id=categories.get("Clothing"),
        expense_kind=ExpenseKind.OCCASIONAL.value,
        event_name="Diwali 2026 Celebration"
    )

    # 6. Budgets
    print("Setting monthly budget...")
    BudgetService.create_budget(
        name="Household Monthly Budget",
        period_type="Monthly",
        start_date=date(today.year, today.month, 1),
        end_date=date(today.year, today.month, 28),
        total_budget_paise=6500000, # ₹65,000
        category_allocations={}
    )

    # 7. Savings Goals
    print("Setting savings goals...")
    SavingsService.create_goal(
        user_id=admin.id,
        goal_name="Emergency Rainy Day Fund",
        target_amount_paise=30000000, # ₹3,00,000
        start_date=today - timedelta(days=60),
        target_date=today + timedelta(days=300),
        monthly_contribution_paise=2500000, # ₹25,000
        priority=GoalPriority.CRITICAL.value
    )

    # 8. Investments
    print("Creating investment assets...")
    InvestmentService.add_investment(
        user_id=admin.id,
        investment_name="UTI Nifty 50 Index Mutual Fund",
        investment_type="Mutual Funds (SIP)",
        invested_amount_paise=18000000, # ₹1,80,000
        current_value_paise=21500000,   # ₹2,15,000
        investment_date=today - timedelta(days=365),
        institution="UTI Mutual Fund"
    )
    InvestmentService.add_investment(
        user_id=spouse.id,
        investment_name="RBI Sovereign Gold Bond 2024",
        investment_type="Gold / SGB",
        invested_amount_paise=10000000, # ₹1,00,000
        current_value_paise=12200000,   # ₹1,22,000
        investment_date=today - timedelta(days=180),
        institution="RBI"
    )

    # 9. Loans & EMIs
    print("Setting up active loans...")
    LoanService.create_loan(
        loan_name="SBI Term Home Loan",
        lender="State Bank of India",
        principal_amount_paise=350000000, # ₹35,00,000
        interest_rate_percent=8.65,
        loan_start_date=today - timedelta(days=730),
        tenure_months=240, # 20 Years
        emi_due_day=5
    )

    AuthService.logout()
    print("Demo dataset generation completed successfully!")

if __name__ == "__main__":
    generate_demo_dataset()
