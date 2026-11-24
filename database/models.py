"""
Kanakkupulla Database Models
All monetary amounts are stored in Integer Paise (1 INR = 100 paise) to prevent floating-point discrepancies.
All dates/datetimes stored as ISO strings or Python Date/DateTime objects.
"""
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, ForeignKey, 
    Text, Index, Float, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database.connection import Base
from config.constants import UserRole, AccountType, TransactionType, LoanStatus, GoalPriority

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.STANDARD.value, nullable=False)
    pin_hash = Column(String(255), nullable=True)
    profile_photo = Column(String(255), nullable=True)
    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_transactions = relationship("Transaction", foreign_keys="Transaction.created_by_id", back_populates="created_by")
    paid_transactions = relationship("Transaction", foreign_keys="Transaction.paid_by_id", back_populates="paid_by")
    beneficiary_transactions = relationship("Transaction", foreign_keys="Transaction.expense_for_id", back_populates="expense_for")
    savings_goals = relationship("SavingsGoal", back_populates="user")
    investments = relationship("Investment", back_populates="user")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    icon = Column(String(50), default="folder")
    color = Column(String(20), default="#4361ee")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    subcategories = relationship("Subcategory", back_populates="category", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="category")
    budget_items = relationship("BudgetCategory", back_populates="category")

class Subcategory(Base):
    __tablename__ = "subcategories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    category = relationship("Category", back_populates="subcategories")
    transactions = relationship("Transaction", back_populates="subcategory")

    __table_args__ = (
        UniqueConstraint("category_id", "name", name="uq_category_subcategory"),
    )

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    account_type = Column(String(50), default=AccountType.SAVINGS.value, nullable=False)
    account_number_masked = Column(String(30), nullable=True) # e.g. "XX-1234"
    institution_name = Column(String(100), nullable=True)
    # Stored in paise (integer): 1000.00 INR = 100000 paise
    opening_balance_paise = Column(Integer, default=0, nullable=False)
    current_balance_paise = Column(Integer, default=0, nullable=False)
    credit_limit_paise = Column(Integer, default=0) # For credit cards
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="account")

class Transaction(Base):
    """
    Main Transaction table for daily expenses, occasional expenses, income, transfers.
    Amounts stored in integer paise.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(String(20), default=TransactionType.EXPENSE.value, nullable=False, index=True)
    expense_kind = Column(String(20), default="Daily", nullable=False) # "Daily" or "Occasional"
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Financial details in paise (integer)
    amount_paise = Column(Integer, nullable=False)
    transaction_date = Column(Date, nullable=False, index=True)
    transaction_time = Column(String(8), default="12:00:00")
    
    # Categorization
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id"), nullable=True, index=True)
    
    # Account & Payment details
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    payment_method = Column(String(50), nullable=False) # Cash, UPI, Card, NetBanking, etc.
    reference_no = Column(String(100), nullable=True)
    merchant = Column(String(150), nullable=True)
    location = Column(String(150), nullable=True)
    
    # Occasional / Event association (e.g., "Diwali 2026", "House Renovation")
    event_name = Column(String(150), nullable=True, index=True)

    # Multi-user Attribution
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    paid_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expense_for_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    last_modified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Flags & metadata
    is_recurring = Column(Boolean, default=False)
    recurring_rule_id = Column(Integer, nullable=True)
    is_reconciled = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="transactions")
    subcategory = relationship("Subcategory", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="created_transactions")
    paid_by = relationship("User", foreign_keys=[paid_by_id], back_populates="paid_transactions")
    expense_for = relationship("User", foreign_keys=[expense_for_id], back_populates="beneficiary_transactions")
    attachments = relationship("TransactionAttachment", back_populates="transaction", cascade="all, delete-orphan")

class TransactionAttachment(Base):
    __tablename__ = "transaction_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="attachments")

class AccountTransfer(Base):
    """
    Transfers between owned accounts (does NOT count as expense or income)
    """
    __tablename__ = "account_transfers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount_paise = Column(Integer, nullable=False)
    transfer_date = Column(Date, nullable=False)
    reference_note = Column(String(255), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    period_type = Column(String(20), default="Monthly") # Monthly, Quarterly, Yearly
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_budget_paise = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    category_budgets = relationship("BudgetCategory", back_populates="budget", cascade="all, delete-orphan")

class BudgetCategory(Base):
    __tablename__ = "budget_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    budget_id = Column(Integer, ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    allocated_paise = Column(Integer, nullable=False)

    budget = relationship("Budget", back_populates="category_budgets")
    category = relationship("Category", back_populates="budget_items")

class SavingsGoal(Base):
    __tablename__ = "savings_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_name = Column(String(150), nullable=False)
    target_amount_paise = Column(Integer, nullable=False)
    current_amount_paise = Column(Integer, default=0, nullable=False)
    start_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=False)
    monthly_contribution_paise = Column(Integer, default=0)
    priority = Column(String(20), default=GoalPriority.MEDIUM.value)
    is_completed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="savings_goals")
    contributions = relationship("SavingsContribution", back_populates="goal", cascade="all, delete-orphan")

class SavingsContribution(Base):
    __tablename__ = "savings_contributions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(Integer, ForeignKey("savings_goals.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    amount_paise = Column(Integer, nullable=False)
    contribution_date = Column(Date, nullable=False)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    goal = relationship("SavingsGoal", back_populates="contributions")

class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    investment_name = Column(String(150), nullable=False)
    investment_type = Column(String(50), nullable=False) # Mutual Funds, SIP, Stocks, Gold, PPF, etc.
    invested_amount_paise = Column(Integer, nullable=False)
    current_value_paise = Column(Integer, nullable=False)
    investment_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=True)
    institution = Column(String(100), nullable=True)
    folio_or_id = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    last_valuation_date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="investments")

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_name = Column(String(150), nullable=False)
    lender = Column(String(100), nullable=False)
    principal_amount_paise = Column(Integer, nullable=False)
    interest_rate_percent = Column(Float, nullable=False)
    loan_start_date = Column(Date, nullable=False)
    tenure_months = Column(Integer, nullable=False)
    emi_amount_paise = Column(Integer, nullable=False)
    emi_due_day = Column(Integer, default=5) # 1-31
    outstanding_principal_paise = Column(Integer, nullable=False)
    status = Column(String(20), default=LoanStatus.ACTIVE.value)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    payments = relationship("LoanPayment", back_populates="loan", cascade="all, delete-orphan")

class LoanPayment(Base):
    __tablename__ = "loan_payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    payment_date = Column(Date, nullable=False)
    amount_paise = Column(Integer, nullable=False)
    principal_component_paise = Column(Integer, default=0)
    interest_component_paise = Column(Integer, default=0)
    payment_method = Column(String(50), nullable=False)
    reference = Column(String(100), nullable=True)

    loan = relationship("Loan", back_populates="payments")

class RecurringRule(Base):
    __tablename__ = "recurring_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    transaction_type = Column(String(20), default=TransactionType.EXPENSE.value)
    amount_paise = Column(Integer, nullable=False)
    frequency = Column(String(20), nullable=False) # Daily, Weekly, Monthly, Yearly
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    next_due_date = Column(Date, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id"), nullable=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    paid_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expense_for_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String(100), nullable=False)
    entity_name = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), default="localhost")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class ApplicationSetting(Base):
    __tablename__ = "application_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
