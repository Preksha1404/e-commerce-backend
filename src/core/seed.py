from src.core.database import SessionLocal
from src.models.users import User
from src.models.products import Category
from src.utils.functions import get_pwd_hash
from fastapi import HTTPException
import os

admin_email = os.getenv("ADMIN_EMAIL")
admin_password = os.getenv("ADMIN_PASSWORD")

def seed_admin():
    db = SessionLocal()
    try:
        # check if admin exists
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if not existing_admin:
            admin = User(
                full_name="Admin User",
                email=admin_email,
                hashed_password=get_pwd_hash(admin_password),
                role="admin",
                is_active=True,
                is_blocked=False
            )
            db.add(admin)
            db.commit()
        else:
            HTTPException(status_code=400, detail="Admin user already exists")
    finally:
        db.close()

def seed_default_category():
    db = SessionLocal()
    try:
        # Check if 'Default' category already exists
        existing_category = db.query(Category).filter(Category.name == "Default").first()
        if not existing_category:
            default_category = Category(
                name="Default",
                description="Default category for uncategorized products"
            )
            db.add(default_category)
            db.commit()
        else:
            HTTPException(status_code=400, detail="Default category already exists") 
    finally:
        db.close()