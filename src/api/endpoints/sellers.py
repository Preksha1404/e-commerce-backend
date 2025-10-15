from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import SellerCreate, UserResponse, ChangePasswordRequest
from src.utils.functions import get_pwd_hash, verify_pwd
from src.utils.auth import get_current_active_user

router = APIRouter(prefix="/sellers", tags=["Sellers"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserResponse)
def register_seller(seller: SellerCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == seller.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_password = get_pwd_hash(seller.password)
    
    new_user = User(
        email=seller.email,
        full_name=seller.full_name,
        hashed_password=hashed_password,
        phone=seller.phone,
        store_name=seller.store_name,
        store_address=seller.store_address,
        role="seller",
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

    if not verify_pwd(old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    # Update password
    user.hashed_password = get_pwd_hash(new_password)
    db.commit()
    db.refresh(user)

    return {"message": "Password updated successfully"}

@router.post("/logout", response_model=dict)
def seller_logout(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
    ):

    current_user.refresh_token = None
    db.commit()

    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return {"message": "Successfully logged out"}