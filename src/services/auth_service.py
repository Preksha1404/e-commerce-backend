import jwt
import os
from datetime import datetime, timedelta
from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from src.models.users import User
from src.schemas.users import (
    UserLogin,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from src.utils.functions import (
    get_pwd_hash,
    verify_pwd,
    create_access_token,
    create_refresh_token,
    ACCESS_TOKEN_EXPIRE,
    REFRESH_TOKEN_EXPIRE,
    generate_reset_token,
    hash_token,
)
from src.utils.email import send_reset_email

# Environment variables with defaults
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


class AuthService:
    """
    Authentication service handling login, refresh tokens, password resets,
    and logout logic for all user roles.
    """

    # ---------------- LOGIN ----------------
    @staticmethod
    def login(credentials: UserLogin, db: Session):
        user = db.query(User).filter(User.email == credentials.email).first()
        if not user or not verify_pwd(credentials.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is inactive.")

        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Account is blocked.")

        if user.role not in ["customer", "seller", "admin"]:
            raise HTTPException(status_code=403, detail="Not authorized.")

        # Generate tokens
        access_token = create_access_token(
            data={"sub": user.email, "id": user.id, "role": user.role, "type": "access"},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE),
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email, "id": user.id, "role": user.role, "type": "refresh"},
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE),
        )

        user.refresh_token = refresh_token
        db.commit()
        db.refresh(user)

        return user, access_token, refresh_token

    # ---------------- REFRESH TOKEN ----------------
    @staticmethod
    def refresh_token(refresh_token: str, db: Session):
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Missing refresh token")

        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
            email = payload.get("sub")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = db.query(User).filter(User.email == email).first()
        if not user or user.refresh_token != refresh_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Account is blocked.")

        new_access_token = create_access_token(
            data={"sub": user.email, "id": user.id, "role": user.role, "type": "access"},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE),
        )

        return {"access_token": new_access_token, "token_type": "bearer"}

    # ---------------- CHANGE PASSWORD ----------------
    @staticmethod
    def change_password(request: ChangePasswordRequest, current_user: User, db: Session):
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        if user.role == "admin":
            raise HTTPException(status_code=403, detail="Admin users cannot change password")

        if not verify_pwd(request.old_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Old password is incorrect")

        user.hashed_password = get_pwd_hash(request.new_password)
        db.commit()
        db.refresh(user)

        return {"message": "Password updated successfully"}

    # ---------------- FORGOT PASSWORD ----------------
    @staticmethod
    async def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session):
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User with this email does not exist")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user account")
        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Account is blocked")

        reset_token = generate_reset_token()
        hashed_token = hash_token(reset_token)

        user.reset_token = hashed_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()

        background_tasks.add_task(send_reset_email, request.email, reset_token)

        return {"message": "A password reset link has been sent to your email."}

    # ---------------- RESET PASSWORD ----------------
    @staticmethod
    async def reset_password(request: ResetPasswordRequest, db: Session):
        hashed_token = hash_token(request.token)
        user = db.query(User).filter(User.reset_token == hashed_token).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")

        if not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Reset token has expired")

        user.hashed_password = get_pwd_hash(request.new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        db.refresh(user)

        return {"message": "Password has been reset successfully"}

    # ---------------- LOGOUT ----------------
    @staticmethod
    def logout(current_user: User, db: Session):
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.refresh_token = None
        db.commit()
        return {"message": "Successfully logged out"}
