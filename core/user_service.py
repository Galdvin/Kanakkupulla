"""
User Management Service for Multi-User Personal Finance
Allows creating, editing, and listing users with Admin, Standard, and Viewer roles.
"""
from typing import List, Optional, Tuple
from database.connection import SessionLocal
from database.models import User, AuditLog
from database.seed import hash_password
from core.authentication import AuthService
from config.constants import UserRole

class UserService:
    @staticmethod
    def get_all_users() -> List[User]:
        db = SessionLocal()
        try:
            return db.query(User).order_by(User.id).all()
        finally:
            db.close()

    @staticmethod
    def get_active_users() -> List[User]:
        db = SessionLocal()
        try:
            return db.query(User).filter_by(status="active").order_by(User.full_name).all()
        finally:
            db.close()

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        db = SessionLocal()
        try:
            return db.query(User).filter_by(id=user_id).first()
        finally:
            db.close()

    @staticmethod
    def create_user(username: str, full_name: str, password: str, role: str = UserRole.STANDARD.value, profile_photo: Optional[str] = None) -> Tuple[bool, str, Optional[User]]:
        current = AuthService.get_current_user()
        if current and not AuthService.is_admin():
            return False, "Only Administrators can create new users", None

        username = username.strip().lower()
        if not username or not full_name:
            return False, "Username and Full Name are required", None

        if len(password) < 6:
            return False, "Password must be at least 6 characters long", None

        db = SessionLocal()
        try:
            existing = db.query(User).filter_by(username=username).first()
            if existing:
                return False, f"Username '{username}' already exists", None

            new_user = User(
                username=username,
                full_name=full_name.strip(),
                password_hash=hash_password(password),
                role=role,
                status="active"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            db.expunge(new_user)

            # Audit
            log = AuditLog(
                user_id=current.id if current else None,
                action="USER_CREATED",
                entity_name="USER",
                entity_id=new_user.id,
                details=f"Created user {username} with role {role}"
            )
            db.add(log)
            db.commit()

            return True, "User created successfully", new_user
        except Exception as e:
            db.rollback()
            return False, f"Database error: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def update_user(user_id: int, full_name: str, role: str, status: str, new_password: Optional[str] = None) -> Tuple[bool, str]:
        current = AuthService.get_current_user()
        if current and not AuthService.is_admin() and current.id != user_id:
            return False, "Unauthorized to update this user"

        db = SessionLocal()
        try:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return False, "User not found"

            # Prevent removing the last active admin
            if user.role in [UserRole.ADMIN.value, "Family Administrator"] and (role not in [UserRole.ADMIN.value, "Family Administrator"] or status != "active"):
                admin_count = db.query(User).filter(User.role.in_([UserRole.ADMIN.value, "Family Administrator"]), User.status == "active", User.id != user_id).count()
                if admin_count == 0:
                    return False, "Cannot deactivate or demote the sole active Administrator"

            user.full_name = full_name.strip()
            if current and AuthService.is_admin():
                user.role = role
                user.status = status

            if new_password and len(new_password) >= 6:
                user.password_hash = hash_password(new_password)

            db.commit()

            log = AuditLog(
                user_id=current.id if current else None,
                action="USER_UPDATED",
                entity_name="USER",
                entity_id=user.id,
                details=f"Updated user {user.username}"
            )
            db.add(log)
            db.commit()

            return True, "User updated successfully"
        except Exception as e:
            db.rollback()
            return False, f"Error: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def delete_user(user_id: int) -> Tuple[bool, str]:
        current = AuthService.get_current_user()
        if not AuthService.is_admin():
            return False, "Unauthorized to delete users"
        if current and current.id == user_id:
            return False, "Cannot delete your own active administrator account"
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                return False, "User not found"
            user.status = "disabled"
            db.commit()

            log = AuditLog(
                user_id=current.id if current else None,
                action="USER_DISABLED",
                entity_name="USER",
                entity_id=user.id,
                details=f"Disabled user account {user.username}"
            )
            db.add(log)
            db.commit()
            return True, "User deactivated successfully"
        except Exception as e:
            db.rollback()
            return False, f"Error: {str(e)}"
        finally:
            db.close()
