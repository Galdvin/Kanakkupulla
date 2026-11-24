"""
Family and Member Management Service:
Separates Login Accounts (users) from Family Members (financial entities).
Example: A child or elder can have financial activity without requiring login credentials.
"""
from typing import List, Optional, Tuple
from database.connection import SessionLocal
from database.models import FamilyProfile, FamilyMember, User, AuditLog
from core.authentication import AuthService, hash_password

class FamilyService:
    @staticmethod
    def get_or_create_default_family() -> FamilyProfile:
        db = SessionLocal()
        try:
            fam = db.query(FamilyProfile).first()
            if not fam:
                fam = FamilyProfile(family_name="My Family")
                db.add(fam)
                db.commit()
                db.refresh(fam)
            db.expunge(fam)
            return fam
        finally:
            db.close()

    @staticmethod
    def get_all_members() -> List[FamilyMember]:
        db = SessionLocal()
        try:
            members = db.query(FamilyMember).filter_by(is_active=True).order_by(FamilyMember.id).all()
            for m in members:
                db.expunge(m)
            return members
        finally:
            db.close()

    @staticmethod
    def add_family_member(name: str, relationship: str = "Member", create_login: bool = False, username: Optional[str] = None, password: Optional[str] = None, role: str = "Family Member") -> Tuple[bool, str, Optional[FamilyMember]]:
        name = name.strip()
        if not name:
            return False, "Member name is required", None

        db = SessionLocal()
        try:
            fam = db.query(FamilyProfile).first()
            if not fam:
                fam = FamilyProfile(family_name="My Family")
                db.add(fam)
                db.flush()

            user_id = None
            if create_login:
                if not username or not password:
                    return False, "Username and password required to create login", None
                existing_user = db.query(User).filter_by(username=username.strip().lower()).first()
                if existing_user:
                    return False, f"Username '{username}' already taken", None

                new_user = User(
                    family_id=fam.id,
                    username=username.strip().lower(),
                    full_name=name,
                    password_hash=hash_password(password),
                    role=role,
                    status="active"
                )
                db.add(new_user)
                db.flush()
                user_id = new_user.id

            member = FamilyMember(
                family_id=fam.id,
                name=name,
                relationship=relationship,
                user_id=user_id,
                is_active=True
            )
            db.add(member)
            db.commit()
            db.refresh(member)
            db.expunge(member)
            return True, "Family member added successfully", member
        except Exception as e:
            db.rollback()
            return False, str(e), None
        finally:
            db.close()
