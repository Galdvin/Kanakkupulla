"""
Kanakkupulla Database Models (Version 2.0 - Family Finance Platform)
Implements:
1. family_profiles & family_members (separating login users from family member financial entities)
2. users & permissions with Argon2 security
3. Double-entry ledger: financial_transactions and ledger_entries (Debit == Credit)
4. Accounts, Categories, Budgets, Savings, Investments, Loans, Recurring rules, and Audit Logs
All money stored in integer paise.
"""
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, ForeignKey, 
    Text, Index, Float, UniqueConstraint, BigInteger
)
from sqlalchemy.orm import relationship
from database.connection import Base
from config.constants import UserRole, AccountType, TransactionType, LoanStatus, GoalPriority

class FamilyProfile(Base):
    __tablename__ = "family_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    family_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("FamilyMember", back_populates="family")
    users = relationship("User", back_populates="family")

class FamilyMember(Base):
    """
    Financial entity within the family (Father, Mother, Child, etc.)
    Can have transactions attributed even without having a login account.
    """
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    family_id = Column(Integer, ForeignKey("family_profiles.id"), nullable=False)
    name = Column(String(100), nullable=False)
    relation_type = Column(String(50), default="Member") # Primary, Spouse, Child, Parent, etc.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Optional link to login user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    family = relationship("FamilyProfile", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="member_profile")
    
    paid_transactions = relationship("FinancialTransaction", foreign_keys="FinancialTransaction.paid_by_member_id", back_populates="paid_by_member")
    beneficiary_transactions = relationship("FinancialTransaction", foreign_keys="FinancialTransaction.expense_for_member_id", back_populates="expense_for_member")

class User(Base):
    """Login accounts with role-based access control and Argon2 password hashing"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    family_id = Column(Integer, ForeignKey("family_profiles.id"), nullable=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False) # Argon2id hash
    role = Column(String(30), default="Family Member", nullable=False) # Family Administrator, Family Member, Viewer
    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    family = relationship("FamilyProfile", back_populates="users")
    member_profile = relationship("FamilyMember", foreign_keys="FamilyMember.user_id", back_populates="user", uselist=False)
    created_transactions = relationship("FinancialTransaction", foreign_keys="FinancialTransaction.created_by_user_id", back_populates="created_by_user")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category_type = Column(String(20), default="Expense") # Expense or Income
    icon = Column(String(50), default="folder")
    color = Column(String(20), default="#0d9488")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    subcategories = relationship("Subcategory", back_populates="category", cascade="all, delete-orphan")
    transactions = relationship("FinancialTransaction", back_populates="category")
    budget_items = relationship("BudgetCategory", back_populates="category")

class Subcategory(Base):
    __tablename__ = "subcategories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    category = relationship("Category", back_populates="subcategories")
    transactions = relationship("FinancialTransaction", back_populates="subcategory")

    __table_args__ = (
        UniqueConstraint("category_id", "name", name="uq_category_subcategory"),
    )

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    account_type = Column(String(50), default=AccountType.SAVINGS.value, nullable=False)
    account_number_masked = Column(String(30), nullable=True)
    institution_name = Column(String(100), nullable=True)
    
    # Precision integer paise
    opening_balance_paise = Column(BigInteger, default=0, nullable=False)
    current_balance_paise = Column(BigInteger, default=0, nullable=False)
    credit_limit_paise = Column(BigInteger, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ledger_entries = relationship("LedgerEntry", back_populates="account")
    transactions = relationship("FinancialTransaction", back_populates="account")

class FinancialTransaction(Base):
    """
    Financial Transaction Master
    Separates creator (user), payer (member), and beneficiary (member).
    """
    __tablename__ = "financial_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(String(30), default=TransactionType.EXPENSE.value, nullable=False, index=True)
    expense_kind = Column(String(30), default="Daily", nullable=False) # Daily or Occasional
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    amount_paise = Column(BigInteger, nullable=False)
    transaction_date = Column(Date, nullable=False, index=True)
    transaction_time = Column(String(8), default="12:00:00")
    
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id"), nullable=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    payment_method = Column(String(50), nullable=False)
    reference_no = Column(String(100), nullable=True)
    merchant = Column(String(150), nullable=True)
    location = Column(String(150), nullable=True)
    event_name = Column(String(150), nullable=True, index=True)

    # Ownership & Attribution
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    paid_by_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False, index=True)
    expense_for_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False, index=True)
    last_modified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    is_recurring = Column(Boolean, default=False)
    is_reconciled = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("Category", back_populates="transactions")
    subcategory = relationship("Subcategory", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id], back_populates="created_transactions")
    paid_by_member = relationship("FamilyMember", foreign_keys=[paid_by_member_id], back_populates="paid_transactions")
    expense_for_member = relationship("FamilyMember", foreign_keys=[expense_for_member_id], back_populates="beneficiary_transactions")
    
    ledger_entries = relationship("LedgerEntry", back_populates="transaction", cascade="all, delete-orphan")
    attachments = relationship("TransactionAttachment", back_populates="transaction", cascade="all, delete-orphan")

class LedgerEntry(Base):
    """
    Balanced Double-Entry Journal:
    Every financial movement has matched debit and credit entries.
    Total Debits == Total Credits.
    """
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("financial_transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    entry_type = Column(String(10), nullable=False) # 'DEBIT' or 'CREDIT'
    amount_paise = Column(BigInteger, nullable=False)
    entry_date = Column(Date, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("FinancialTransaction", back_populates="ledger_entries")
    account = relationship("Account", back_populates="ledger_entries")

class TransactionAttachment(Base):
    __tablename__ = "transaction_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("financial_transactions.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("FinancialTransaction", back_populates="attachments")

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    period_type = Column(String(20), default="Monthly")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_budget_paise = Column(BigInteger, nullable=False)
    family_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=True) # Shared or individual budget
    created_at = Column(DateTime, default=datetime.utcnow)

    category_budgets = relationship("BudgetCategory", back_populates="budget", cascade="all, delete-orphan")

class BudgetCategory(Base):
    __tablename__ = "budget_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    budget_id = Column(Integer, ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    allocated_paise = Column(BigInteger, nullable=False)

    budget = relationship("Budget", back_populates="category_budgets")
    category = relationship("Category", back_populates="budget_items")

class SavingsGoal(Base):
    __tablename__ = "savings_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    family_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False)
    goal_name = Column(String(150), nullable=False)
    target_amount_paise = Column(BigInteger, nullable=False)
    current_amount_paise = Column(BigInteger, default=0, nullable=False)
    start_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=False)
    monthly_contribution_paise = Column(BigInteger, default=0)
    priority = Column(String(20), default=GoalPriority.MEDIUM.value)
    is_completed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    contributions = relationship("SavingsContribution", back_populates="goal", cascade="all, delete-orphan")

class SavingsContribution(Base):
    __tablename__ = "savings_contributions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(Integer, ForeignKey("savings_goals.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    amount_paise = Column(BigInteger, nullable=False)
    contribution_date = Column(Date, nullable=False)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    goal = relationship("SavingsGoal", back_populates="contributions")

class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    family_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False)
    investment_name = Column(String(150), nullable=False)
    investment_type = Column(String(50), nullable=False)
    invested_amount_paise = Column(BigInteger, nullable=False)
    current_value_paise = Column(BigInteger, nullable=False)
    investment_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=True)
    institution = Column(String(100), nullable=True)
    folio_or_id = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    last_valuation_date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    family_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=True)
    loan_name = Column(String(150), nullable=False)
    lender = Column(String(100), nullable=False)
    principal_amount_paise = Column(BigInteger, nullable=False)
    interest_rate_percent = Column(Float, nullable=False)
    loan_start_date = Column(Date, nullable=False)
    tenure_months = Column(Integer, nullable=False)
    emi_amount_paise = Column(BigInteger, nullable=False)
    emi_due_day = Column(Integer, default=5)
    outstanding_principal_paise = Column(BigInteger, nullable=False)
    status = Column(String(20), default=LoanStatus.ACTIVE.value)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    payments = relationship("LoanPayment", back_populates="loan", cascade="all, delete-orphan")

class LoanPayment(Base):
    __tablename__ = "loan_payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    payment_date = Column(Date, nullable=False)
    amount_paise = Column(BigInteger, nullable=False)
    principal_component_paise = Column(BigInteger, default=0)
    interest_component_paise = Column(BigInteger, default=0)
    payment_method = Column(String(50), nullable=False)
    reference = Column(String(100), nullable=True)

    loan = relationship("Loan", back_populates="payments")

class RecurringRule(Base):
    __tablename__ = "recurring_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    transaction_type = Column(String(20), default=TransactionType.EXPENSE.value)
    amount_paise = Column(BigInteger, nullable=False)
    frequency = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    next_due_date = Column(Date, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id"), nullable=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    paid_by_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False)
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
