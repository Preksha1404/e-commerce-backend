from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from src.models.users import User
from src.schemas.users import UserCreate

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
