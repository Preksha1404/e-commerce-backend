from fastapi import APIRouter, Depends, Response, Cookie, BackgroundTasks, HTTPException, status # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from sqlalchemy.orm import Session # type: ignore
from dotenv import load_dotenv # type: ignore
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
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Auth"])

load_dotenv()

<<<<<<< HEAD
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

=======
SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")
>>>>>>> b3ea0263ad5a6cf78871dd416363497b46549c41

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- LOGIN ----------------
@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user, access_token, refresh_token = AuthService.login(credentials, db)

     
    
    content = {
        "user": UserResponse.model_validate(user).model_dump(),
        "message": "Login successful"
    }

    response = JSONResponse(content=content)
<<<<<<< HEAD
    response.set_cookie("access_token", access_token, httponly=True, secure=True, samesite="None")
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=True, samesite="None")
=======

    response.set_cookie("access_token", access, httponly=True, secure=True, samesite="None")
    response.set_cookie("refresh_token", refresh, httponly=True, secure=True, samesite="None")
>>>>>>> b3ea0263ad5a6cf78871dd416363497b46549c41

    return response


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
