import jwt
import os
from datetime import datetime, timedelta
from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import UserLogin, ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest
from src.utils.functions import get_pwd_hash, verify_pwd, create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE, REFRESH_TOKEN_EXPIRE, generate_reset_token, hash_token
from src.services.email_service import send_email
from src.utils.email_templates import password_reset_template

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

class AuthService:

    @staticmethod
    def login(credentials: UserLogin, db: Session):
        """
        Authenticate user and return user object, access token, and refresh token.
        Returns: tuple (user, access_token, refresh_token)
        """
        user = db.query(User).filter(User.email == credentials.email).first()

        if not user or not verify_pwd(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.role not in ["customer", "seller", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to login here"
            )

        # Check if seller is inactive
        if user.role == "seller" and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is under approval process"
            )

        # Check if seller or customer is blocked
        if user.role in ["seller", "customer"] and user.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is blocked"
            )

        access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE)
        access_token = create_access_token(
            data={
                "id": user.id,
                "email": user.email,
                "role": user.role
            },
            expires_delta=access_token_expires
        )

        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE)
        refresh_token = create_refresh_token(
            data={
                "id": user.id,
                "email": user.email,
                "role": user.role
            },
            expires_delta=refresh_token_expires
        )

        user.refresh_token = refresh_token
        db.commit()
        db.refresh(user)

        return user, access_token, refresh_token

    @staticmethod
    def refresh_token(refresh_token: str, db: Session):
        """
        Validate refresh token and generate new access token.
        Returns: new access token
        """
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Missing refresh token")

        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = db.query(User).filter(User.email == email).first()
        if not user or user.refresh_token != refresh_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access_token = create_access_token({"sub": user.email, "role": user.role})

        return new_access_token
    
    @staticmethod
    def change_password(request: ChangePasswordRequest, current_user: User, db: Session):
        """
        Change user password.
        """
        user = db.query(User).filter(User.id == current_user.id).first()

        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        if user.role == "admin":
            raise HTTPException(status_code=403, detail="Admin users cannot change their password")
        
        old_password = request.old_password
        new_password = request.new_password

        if not old_password or not new_password:
            raise HTTPException(status_code=400, detail="Old and new passwords are required")

        if not verify_pwd(old_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Old password is incorrect")

        user.hashed_password = get_pwd_hash(new_password)
        
        db.commit()
        db.refresh(user)

        return {"message": "Password updated successfully"}

    @staticmethod
    async def forgot_password(request, background_tasks: BackgroundTasks, db: Session):
        """
        Step 1: Request password reset
        - Receives email
        - Generates token
        - Sends reset email
        """
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this email does not exist"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )
        
        # Generate token and save hashed token
        reset_token = generate_reset_token()
        hashed_token = hash_token(reset_token)
        
        user.reset_token = hashed_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()

        # Generate email template
        subject, html_content = password_reset_template(user.email, reset_token)

        # Send reset email in background using generic sender
        await send_email(background_tasks, to_email=user.email, subject=subject, html_content=html_content)

        return {"message": "A reset link has been sent to your email"}
    
    @staticmethod
    async def reset_password(request: ResetPasswordRequest, db: Session):
        """
        Step 2: Reset password with token
        - Validates token
        - Checks expiration
        - Updates password
        """
        hashed_token = hash_token(request.token)
        
        user = db.query(User).filter(User.reset_token == hashed_token).first()
        
        if not user:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired reset token"
            )
        
        if not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
            raise HTTPException(
                status_code=400,
                detail="Reset token has expired"
            )

        user.hashed_password = get_pwd_hash(request.new_password)
        user.reset_token = None
        user.reset_token_expires = None
        
        db.commit()
        db.refresh(user)
        
        return {"message": "Password has been reset successfully"}
    
    @staticmethod
    def logout(current_user: User, db: Session):
        """
        Clear refresh token from database.
        """
        current_user.refresh_token = None
        db.commit()

        return {"message": "Successfully logged out"}