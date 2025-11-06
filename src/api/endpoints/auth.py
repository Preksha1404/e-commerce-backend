from fastapi import APIRouter, Depends, Response, Cookie, BackgroundTasks, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import UserLogin, UserResponse, ChangePasswordRequest,ForgotPasswordRequest, ResetPasswordRequest
from src.utils.auth import get_current_active_user
from dotenv import load_dotenv
import os
from src.services.auth_service import AuthService
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Auth"])

load_dotenv()

SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login(credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    user, access, refresh = AuthService.login(credentials, db)

    content = {
        "user": UserResponse.model_validate(user).model_dump(),
        "message": "Login successful"
    }

    response = JSONResponse(content=content)

    response.set_cookie("access_token", access, httponly=True, secure=True, samesite="None")
    response.set_cookie("refresh_token", refresh, httponly=True, secure=True, samesite="None")

    return response

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.post("/refresh")
def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, include_in_schema=False),
    db: Session = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access = AuthService.refresh_token(refresh_token, db)
    response.set_cookie("access_token", new_access, httponly=True)
    return {"access_token": new_access}

@router.patch('/change-password', response_model=dict)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return AuthService.change_password(request, current_user, db)

@router.post("/forget-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    return await AuthService.forgot_password(request, background_tasks, db)

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    return await AuthService.reset_password(request, db)

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