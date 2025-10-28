from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.user import User
from src.schemas.users import UserCreate, UserResponse, ChangePasswordRequest
from src.utils.functions import get_pwd_hash, verify_pwd
from src.utils.auth import get_current_active_user

router = APIRouter(prefix="/users", tags=["Users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="User already exists")
    
    hashed_password = get_pwd_hash(user.password)
    
    new_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        phone=user.phone,
        role="customer",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.patch('/change-password', response_model=dict)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    user=db.query(User).filter(User.id==current_user.id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Access request attributes correctly
    old_password = request.old_password
    new_password = request.new_password

    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="Old and new passwords are required")

    if not verify_pwd(old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    # Update password
    user.hashed_password = get_pwd_hash(new_password)
    db.commit()
    db.refresh(user)

    return {"message": "Password updated successfully"}

@router.post("/logout", response_model=dict)
def user_logout(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
    ):

    current_user.refresh_token = None
    db.commit()

    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    
    return {"message": "Successfully logged out"}