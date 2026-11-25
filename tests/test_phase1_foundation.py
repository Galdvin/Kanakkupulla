"""
Tests for Phase 1 Foundation:
- Database creation & integrity
- Password hashing & verification
- Authentication service (login success, failure, role check)
- User service (CRUD, constraints)
- Currency and financial formatting utilities
"""
import pytest
from datetime import datetime
from database.connection import Base, engine, SessionLocal
from database.models import User, Category, Account
from database.seed import hash_password, verify_password, seed_database
from core.authentication import AuthService
from core.user_service import UserService
from core.financial_utils import inr_to_paise, paise_to_inr, format_inr, format_date, parse_date
from config.constants import UserRole

def test_financial_utils_conversion():
    assert inr_to_paise(100) == 10000
    assert inr_to_paise("1250.50") == 125050
    assert inr_to_paise(0.05) == 5
    assert paise_to_inr(125050) == 1250.50

def test_indian_currency_formatting():
    # Standard Indian formatting tests
    assert format_inr(100000) == "₹1,000.00"
    assert format_inr(10000000) == "₹1,00,000.00"
    assert format_inr(1000000000) == "₹1,00,00,000.00"
    assert format_inr(50) == "₹0.50"
    assert format_inr(-50000) == "-₹500.00"

def test_password_hashing():
    pwd = "SecretPassword123"
    h = hash_password(pwd)
    assert h != pwd
    assert verify_password(pwd, h) is True
    assert verify_password("WrongPassword", h) is False

def test_authentication_service():
    # Admin is seeded with admin123
    success, msg, user = AuthService.login("admin", "admin123")
    assert success is True
    assert user is not None
    assert user.role in [UserRole.ADMIN.value, "Family Administrator", "admin"]
    assert AuthService.is_admin() is True

    # Failed login
    fail_success, fail_msg, _ = AuthService.login("admin", "wrongpass")
    assert fail_success is False
    assert "Invalid" in fail_msg

    AuthService.logout()
    assert AuthService.get_current_user() is None

def test_user_service_crud():
    # Login as admin first
    AuthService.login("admin", "admin123")
    test_uname = f"spouse_test_{int(datetime.now().timestamp())}"

    # Create new family member
    ok, msg, new_user = UserService.create_user(
        username=test_uname,
        full_name="Priya Kumar",
        password="password123",
        role=UserRole.STANDARD.value
    )
    assert ok is True
    assert new_user.username == test_uname
    assert new_user.full_name == "Priya Kumar"

    # Verify duplicate username prevented
    dup_ok, dup_msg, _ = UserService.create_user(
        username=test_uname,
        full_name="Duplicate",
        password="password123"
    )
    assert dup_ok is False
    assert "already exists" in dup_msg

    # Update user
    update_ok, update_msg = UserService.update_user(
        user_id=new_user.id,
        full_name="Priya A. Kumar",
        role=UserRole.STANDARD.value,
        status="active"
    )
    assert update_ok is True
    updated = UserService.get_user_by_id(new_user.id)
    assert updated.full_name == "Priya A. Kumar"

    AuthService.logout()
