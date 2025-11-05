from fastapi import APIRouter, Depends, Response, Cookie, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import (
    UserLogin,
    UserResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from src.utils.auth import get_current_active_user
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- LOGIN ----------------
@router.post("/login")
def login(credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    result = AuthService.login(credentials, db)

    content = {
        "user": result["user"],
        "message": "Login successful"
    }

    json_response = JSONResponse(content=content)

    # Store tokens in secure HTTP-only cookies
    json_response.set_cookie(
        "access_token",
        result["access_token"],
        httponly=True,
        secure=True,
        samesite="None"
    )
    json_response.set_cookie(
        "refresh_token",
        result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="None"
    )

    return json_response


# ---------------- PROFILE ----------------
@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_active_user)):
    return current_user


# ---------------- REFRESH TOKEN ----------------
@router.post("/refresh")
def refresh(
    response: Response,
    refresh_token: str = Cookie(...),
    db: Session = Depends(get_db)
):
    new_access = AuthService.refresh_token(refresh_token, db)
    response.set_cookie("access_token", new_access["access_token"], httponly=True)
    return new_access


# ---------------- CHANGE PASSWORD ----------------
@router.patch("/change-password", response_model=dict)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return AuthService.change_password(request, current_user, db)


# ---------------- FORGOT PASSWORD ----------------
@router.post("/forget-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    return await AuthService.forgot_password(request, background_tasks, db)


# ---------------- RESET PASSWORD ----------------
@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    return await AuthService.reset_password(request, db)


# ---------------- LOGOUT ----------------
@router.post("/logout")
def logout(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    AuthService.logout(current_user, db)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}
