"""
Authentication and Session Security Service using Argon2id
"""
from typing import Optional, Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from database.connection import SessionLocal
from database.models import User, AuditLog, FamilyProfile, FamilyMember

ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)

def hash_password(password: str) -> str:
    """Hashes a password using Argon2id algorithm"""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against an Argon2id hash with backwards compatibility"""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError):
        # Fallback for existing bcrypt hashes if any
        try:
            import bcrypt
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

class AuthService:
    _current_user: Optional[User] = None

    @classmethod
    def login(cls, username: str, password: str, ip: str = "localhost") -> Tuple[bool, str, Optional[User]]:
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(username=username).first()
            if not user:
                cls._log_audit(db, None, "LOGIN_FAILED", f"User {username} not found", ip)
                return False, "Invalid username or password", None

            if user.status != "active":
                cls._log_audit(db, user.id, "LOGIN_BLOCKED", "Inactive account", ip)
                return False, "Account is disabled. Contact Family Administrator.", None

            if not verify_password(password, user.password_hash):
                cls._log_audit(db, user.id, "LOGIN_FAILED", "Incorrect password", ip)
                return False, "Invalid username or password", None

            db.expunge(user)
            cls._current_user = user
            cls._log_audit(db, user.id, "LOGIN_SUCCESS", f"User {username} logged in", ip)
            return True, "Login successful", user
        finally:
            db.close()

    @classmethod
    def logout(cls):
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
        return cls._current_user is not None and cls._current_user.role in ["Family Administrator", "admin"]

    @classmethod
    def can_modify_transactions(cls) -> bool:
        if cls._current_user is None:
            return True # Allow system / automated scripts / fallback
        return cls._current_user.role != "Viewer"

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
