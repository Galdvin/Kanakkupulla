"""
Pytest Fixtures and Session Configuration:
Drops and re-creates all SQLite tables before each test on isolated test database.
"""
import os
os.environ["TESTING"] = "1"

import pytest
from database.connection import Base, engine, SessionLocal
from database.seed import seed_database
from core.authentication import AuthService

from sqlalchemy import text

@pytest.fixture(autouse=True)
def clean_db():
    assert "test" in str(engine.url), f"CRITICAL ABORT: Refusing to clean non-test database: {engine.url}"
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.execute(text("PRAGMA foreign_keys = OFF;"))
        # Clear tables
        tables = [
            "ledger_entries", "transaction_attachments", "financial_transactions",
            "savings_contributions", "savings_goals", "investments", "loan_payments", "loans",
            "budget_categories", "budgets", "recurring_rules", "audit_logs", "subcategories",
            "categories", "accounts", "family_members", "users", "family_profiles"
        ]
        for t in tables:
            db.execute(text(f"DELETE FROM {t};"))
        db.execute(text("PRAGMA foreign_keys = ON;"))
        db.commit()
    finally:
        db.close()

    seed_database()
    yield
    AuthService.logout()
