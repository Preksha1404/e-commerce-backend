import secrets
import os
from datetime import datetime, timedelta
import dotenv
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from pyd import BaseModel
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
dotenv.load_dotenv()
from src.core.database import get_db
from src.models.user import User
from src.core.dependencies import get_current_user, admin_required
from src.utils.security import hash_password


router = APIRouter(prefix="/api/users", tags=["Users"])
 
class ForgotPasswordSchema(BaseModel):
    email: str

class ResetPasswordSchema(BaseModel):
    token: str
    new_password: str
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)
 
@router.get("/me")
async def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "is_blocked": current_user.is_blocked,
        "profile_picture": current_user.profile_picture,
    }

@router.put("/me")
async def update_profile(
    full_name: str = None,
    profile_picture: UploadFile = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if full_name:
        current_user.full_name = full_name
    if profile_picture:
        current_user.profile_picture = profile_picture.filename 
    db.commit()
    db.refresh(current_user)
    return {"message": "Profile updated successfully"}
 
@router.post("/{user_id}/block")
async def block_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_blocked = True
    db.commit()
    return {"message": f"User {user.email} blocked"}

@router.post("/{user_id}/unblock")
async def unblock_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(admin_required)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_blocked = False
    db.commit()
    return {"message": f"User {user.email} unblocked"}

 
@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

 
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=30)

 
    user.reset_password_token = reset_token
    user.reset_password_expires = expires_at
    db.commit()

 
    reset_link = f"http://localhost:8000/reset-password?token={reset_token}"

 
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[data.email],  # any recipient email
        body=f"Hello {user.full_name},\n\nClick the link to reset your password:\n{reset_link}\n\nThis link expires in 30 minutes.",
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)

    return {"message": "Password reset email sent successfully"}

 
@router.post("/reset-password")
async def reset_password(data: ResetPasswordSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_password_token == data.token).first()
    if not user or not user.reset_password_expires:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if user.reset_password_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

 
    user.hashed_password = hash_password(data.new_password)
    user.reset_password_token = None
    user.reset_password_expires = None
    db.commit()

    return {"msg": "Password reset successful"}
