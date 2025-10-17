from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import SellerCreate, SellerResponse
from src.utils.functions import get_pwd_hash
from src.utils.auth import get_current_active_user
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/sellers", tags=["Sellers"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_sellers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
    ):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view sellers"
        )
    sellers = db.query(User).filter(User.role == "seller").all()
    return sellers

@router.post("/register", response_model=SellerResponse)
def register_seller(seller: SellerCreate, db: Session = Depends(get_db)):
    
    # Check if email already exists
    if db.query(User).filter(User.email == seller.email).first():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "error",
                "message": "Email already exists"
            }
        )
    
    hashed_password = get_pwd_hash(seller.password)
    
    new_seller = User(
        email=seller.email,
        full_name=seller.full_name,
        hashed_password=hashed_password,
        phone=seller.phone,
        store_name=seller.store_name,
        store_address=seller.store_address,
        role="seller",
        is_active=False,
        is_blocked=False,
    )
    db.add(new_seller)
    db.commit()
    db.refresh(new_seller)
    return new_seller