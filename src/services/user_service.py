from sqlalchemy.orm import Session
from fastapi import HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from src.models.users import User
from src.schemas.users import UserCreate, UserUpdate
from src.utils.functions import get_pwd_hash
from src.utils.email_templates import customer_welcome_template
from src.services.email_service import send_email

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
    async def register_user(db: Session, user: UserCreate, background_tasks: BackgroundTasks):
        # Check if email already exists
        if db.query(User).filter(User.email == user.email).first():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Email already exists"}
            )

        # Hash password and create new customer
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

        # Generate welcome email template
        subject, html_content = customer_welcome_template(new_user.full_name)

        # Send email using generic sender
        await send_email(
            background_tasks,
            to_email=new_user.email,
            subject=subject,
            html_content=html_content
        )

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
    
    @staticmethod
    def toggle_customer_block(user_id: int, db: Session, current_user: User):
        """
        Admin-only: Toggle customer's active/block status.
        """
        # Only admin can toggle block/unblock
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only admin can block/unblock customers."
            )

        user = db.query(User).filter(User.id == user_id, User.role == "customer").first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Customer not found"
            )

        # Toggle block/unblock status
        user.is_blocked = not user.is_blocked

        db.commit()
        db.refresh(user)

        return user