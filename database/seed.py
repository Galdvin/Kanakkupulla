"""
Database Seeding for Kanakkupulla 2.0 (Family Financial Platform)
Creates default Family Profile, Administrator User, Family Members, Accounts, Categories, and Settings.
Uses Argon2id password hashing.
"""
from datetime import datetime, date
from database.connection import Base, engine, SessionLocal
from database.models import FamilyProfile, FamilyMember, User, Category, Subcategory, Account, ApplicationSetting
from core.authentication import hash_password, verify_password
from config.constants import AccountType, DEFAULT_CATEGORIES
from config.settings import DEFAULT_CURRENCY, DEFAULT_DATE_FORMAT

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Family Profile
        fam = db.query(FamilyProfile).first()
        if not fam:
            fam = FamilyProfile(family_name="My Household")
            db.add(fam)
            db.flush()

        # 2. Family Administrator User
        admin_user = db.query(User).filter_by(username="admin").first()
        if not admin_user:
            admin_user = User(
                family_id=fam.id,
                username="admin",
                full_name="Family Head",
                password_hash=hash_password("admin123"), # Default Argon2 hash
                role="Family Administrator",
                status="active"
            )
            db.add(admin_user)
            db.flush()

        # 3. Family Members
        admin_member = db.query(FamilyMember).filter_by(name="Family Head").first()
        if not admin_member:
            admin_member = FamilyMember(
                family_id=fam.id,
                name="Family Head",
                relation_type="Primary",
                user_id=admin_user.id,
                is_active=True
            )
            db.add(admin_member)

        # 4. Default Categories & Subcategories
        colors = ["#0d9488", "#10b981", "#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#ef4444", "#06b6d4"]
        c_idx = 0
        for cat_name, subcats in DEFAULT_CATEGORIES.items():
            cat = db.query(Category).filter_by(name=cat_name).first()
            if not cat:
                cat = Category(name=cat_name, color=colors[c_idx % len(colors)], is_active=True)
                db.add(cat)
                db.flush()
                c_idx += 1

            for sub_name in subcats:
                sub = db.query(Subcategory).filter_by(category_id=cat.id, name=sub_name).first()
                if not sub:
                    sub = Subcategory(category_id=cat.id, name=sub_name, is_active=True)
                    db.add(sub)

        # 5. Default Accounts
        default_accounts = [
            ("Family Cash Box", AccountType.CASH.value, 1000000), # ₹10,000.00
            ("Primary Joint Bank Account", AccountType.SAVINGS.value, 10000000), # ₹1,00,000.00
            ("Family Emergency Fund", AccountType.SAVINGS.value, 20000000), # ₹2,00,000.00
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

        # 6. Default Settings
        settings_map = {
            "app_theme": "dark",
            "currency": DEFAULT_CURRENCY,
            "date_format": DEFAULT_DATE_FORMAT,
            "session_timeout_minutes": "15"
        }
        for k, v in settings_map.items():
            st = db.query(ApplicationSetting).filter_by(key=k).first()
            if not st:
                db.add(ApplicationSetting(key=k, value=v))

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
