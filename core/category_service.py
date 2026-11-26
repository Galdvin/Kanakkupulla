"""
Category & Subcategory Management Service
Allows dynamic addition, editing, disabling, and fetching of expense categories.
"""
from typing import List, Optional, Tuple
from database.connection import SessionLocal
from database.models import Category, Subcategory, FinancialTransaction, AuditLog
from core.authentication import AuthService

class CategoryService:
    @staticmethod
    def get_all_categories(active_only: bool = True) -> List[Category]:
        db = SessionLocal()
        try:
            q = db.query(Category)
            if active_only:
                q = q.filter_by(is_active=True)
            return q.order_by(Category.name).all()
        finally:
            db.close()

    @staticmethod
    def get_categories_by_type(category_type: str = "Expense", active_only: bool = True) -> List[Category]:
        db = SessionLocal()
        try:
            q = db.query(Category)
            if active_only:
                q = q.filter_by(is_active=True)
            if category_type:
                q = q.filter(Category.category_type.ilike(category_type))
            cats = q.order_by(Category.name).all()
            if not cats and category_type == "Expense":
                # Fallback to all active categories if none specifically tagged
                return db.query(Category).filter_by(is_active=True).order_by(Category.name).all()
            return cats
        finally:
            db.close()

    @staticmethod
    def get_subcategories(category_id: int, active_only: bool = True) -> List[Subcategory]:
        db = SessionLocal()
        try:
            q = db.query(Subcategory).filter_by(category_id=category_id)
            if active_only:
                q = q.filter_by(is_active=True)
            return q.order_by(Subcategory.name).all()
        finally:
            db.close()

    @staticmethod
    def create_category(name: str, color: str = "#38bdf8", icon: str = "folder") -> Tuple[bool, str, Optional[Category]]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized action", None
            
        name = name.strip()
        if not name:
            return False, "Category name cannot be empty", None

        db = SessionLocal()
        try:
            existing = db.query(Category).filter_by(name=name).first()
            if existing:
                db.expunge(existing)
                return True, "Category already exists", existing

            cat = Category(name=name, color=color, icon=icon, is_active=True)
            db.add(cat)
            db.commit()
            db.refresh(cat)
            db.expunge(cat)
            return True, "Category created successfully", cat
        except Exception as e:
            db.rollback()
            return False, str(e), None
        finally:
            db.close()

    @staticmethod
    def add_subcategory(category_id: int, subcategory_name: str) -> Tuple[bool, str, Optional[Subcategory]]:
        if not AuthService.can_modify_transactions():
            return False, "Unauthorized action", None

        subcategory_name = subcategory_name.strip()
        if not subcategory_name:
            return False, "Subcategory name cannot be empty", None

        db = SessionLocal()
        try:
            existing = db.query(Subcategory).filter_by(category_id=category_id, name=subcategory_name).first()
            if existing:
                return False, f"Subcategory '{subcategory_name}' already exists in this category", None

            sub = Subcategory(category_id=category_id, name=subcategory_name, is_active=True)
            db.add(sub)
            db.commit()
            db.refresh(sub)
            db.expunge(sub)
            return True, "Subcategory added successfully", sub
        except Exception as e:
            db.rollback()
            return False, str(e), None
        finally:
            db.close()
