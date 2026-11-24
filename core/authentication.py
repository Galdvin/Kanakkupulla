"""
Authentication and Session Security Service
"""
from typing import Optional
from database.connection import SessionLocal
from database.models import User, AuditLog
from database.seed import hash_password, verify_password
from config.constants import UserRole

class AuthService:
    _current_user: Optional[User] = None

    @classmethod
    def login(cls, username: str, password: str, ip: str = "localhost") -> tuple[bool, str, Optional[User]]:
        """Authenticates user with username & password"""
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(username=username).first()
            if not user:
                cls._log_audit(db, None, "LOGIN_FAILED", f"User {username} not found", ip)
                return False, "Invalid username or password", None

            if user.status != "active":
                cls._log_audit(db, user.id, "LOGIN_BLOCKED", "Inactive/Suspended account", ip)
                return False, "Account is disabled. Contact Administrator.", None

            if not verify_password(password, user.password_hash):
                cls._log_audit(db, user.id, "LOGIN_FAILED", "Incorrect password", ip)
                return False, "Invalid username or password", None

            # Expunge or eager load to keep user object detached safely
            db.expunge(user)
            cls._current_user = user
            cls._log_audit(db, user.id, "LOGIN_SUCCESS", f"User {username} logged in", ip)
            return True, "Login successful", user
        finally:
            db.close()

    @classmethod
    def logout(cls):
        """Logs out the active user"""
        if cls._current_user:
            db = SessionLocal()
            try:
                cls._log_audit(db, cls._current_user.id, "LOGOUT", f"User {cls._current_user.username} logged out")
            finally:
                db.close()
            cls._current_user = None

    @classmethod
    def get_current_user(cls) -> Optional[User]:
        return cls._current_user

    @classmethod
    def is_admin(cls) -> bool:
        return cls._current_user is not None and cls._current_user.role == UserRole.ADMIN.value

    @classmethod
    def can_modify_transactions(cls) -> bool:
        return cls._current_user is not None and cls._current_user.role in [UserRole.ADMIN.value, UserRole.STANDARD.value]

    @classmethod
    def _log_audit(cls, db, user_id: Optional[int], action: str, details: str, ip: str = "localhost"):
        try:
            log = AuditLog(
                user_id=user_id,
                action=action,
                entity_name="AUTH",
                details=details,
                ip_address=ip
            )
            db.add(log)
            db.commit()
        except Exception:
            pass
