"""
Pytest Fixtures and Session Configuration:
Drops and re-creates all SQLite tables before each test for absolute isolation.
"""
import pytest
from database.connection import Base, engine
from database.seed import seed_database
from core.authentication import AuthService

from sqlalchemy import text

@pytest.fixture(autouse=True)
def clean_db():
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF;"))
        conn.commit()
    Base.metadata.drop_all(bind=engine)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON;"))
        conn.commit()
    seed_database()
    yield
    AuthService.logout()
