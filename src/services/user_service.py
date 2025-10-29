from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from src.models.users import User
from src.schemas.users import UserCreate, UserUpdate

from src.utils.functions import get_pwd_hash

class UserService:
    @staticmethod
    def get_all_users(db: Session, current_user: User):
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view all users"
            )
        users = db.query(User).filter(User.role == "customer").all()
        return users

    @staticmethod
    def register_user(db: Session, user: UserCreate):
        # Check if email already exists
        if db.query(User).filter(User.email == user.email).first():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": "Email already exists"
                }
            )

        hashed_password = get_pwd_hash(user.password)
        
        new_user = User(
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            phone=user.phone,
            role="customer",
            is_active=True,
            is_blocked=False,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate,current_user: User):
        """Update user details accessible the user."""
        if current_user.role != "customer" or current_user.id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to update this user"
            )

        user = db.query(User).filter(User.id == user_id, User.role == "customer").first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.phone is not None:
            user.phone = user_update.phone

        db.commit()
        db.refresh(user)
        return user