"""
Database initialization and seeding routines.
Sets up initial admin account, default categories, subcategories, and settings.
"""
import bcrypt
from datetime import datetime, date
from database.connection import Base, engine, SessionLocal
from database.models import User, Category, Subcategory, Account, ApplicationSetting
from config.constants import UserRole, AccountType, DEFAULT_CATEGORIES
from config.settings import DEFAULT_CURRENCY, DEFAULT_DATE_FORMAT

def hash_password(password: str) -> str:
    """Hashes a password with bcrypt salt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against bcrypt hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def seed_database():
    """Seeds default categories, admin user, and basic accounts if empty"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Seed Admin User if not exists
        admin = db.query(User).filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                full_name="Administrator",
                password_hash=hash_password("admin123"), # Default password, prompt to change
                role=UserRole.ADMIN.value,
                status="active"
            )
            db.add(admin)
            db.flush()

        # 2. Seed Default Categories & Subcategories
        category_colors = [
            "#e63946", "#f1faee", "#a8dadc", "#457b9d", "#1d3557",
            "#2a9d8f", "#e76f51", "#f4a261", "#264653", "#8338ec",
            "#3a86ff", "#ff006e", "#fb5607", "#ffbe0b", "#06d6a0",
            "#118ab2", "#073b4c", "#ef476f", "#ffd166", "#06d6a0"
        ]
        color_idx = 0
        for cat_name, subcats in DEFAULT_CATEGORIES.items():
            cat = db.query(Category).filter_by(name=cat_name).first()
            if not cat:
                cat = Category(
                    name=cat_name,
                    color=category_colors[color_idx % len(category_colors)],
                    is_active=True
                )
                db.add(cat)
                db.flush()
                color_idx += 1

            for sub_name in subcats:
                sub = db.query(Subcategory).filter_by(category_id=cat.id, name=sub_name).first()
                if not sub:
                    sub = Subcategory(
                        category_id=cat.id,
                        name=sub_name,
                        is_active=True
                    )
                    db.add(sub)

        # 3. Seed Default Accounts
        default_accounts = [
            ("Cash in Hand", AccountType.CASH.value, 500000), # ₹5,000.00
            ("Primary Bank Account", AccountType.SAVINGS.value, 5000000), # ₹50,000.00
            ("Emergency Fund", AccountType.SAVINGS.value, 10000000), # ₹1,00,000.00
        ]
        for acc_name, acc_type, bal in default_accounts:
            acc = db.query(Account).filter_by(name=acc_name).first()
            if not acc:
                acc = Account(
                    name=acc_name,
                    account_type=acc_type,
                    opening_balance_paise=bal,
                    current_balance_paise=bal,
                    is_active=True
                )
                db.add(acc)

        # 4. Seed Default Settings
        settings_map = {
            "app_theme": "dark",
            "currency": DEFAULT_CURRENCY,
            "date_format": DEFAULT_DATE_FORMAT,
            "session_timeout_minutes": "15",
            "first_run_completed": "true"
        }
        for k, v in settings_map.items():
            setting = db.query(ApplicationSetting).filter_by(key=k).first()
            if not setting:
                setting = ApplicationSetting(key=k, value=v)
                db.add(setting)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
    print("Database schema created and successfully seeded.")
