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

@router.get("/{seller_id}", response_model=SellerResponse)
def get_seller(
    seller_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
    ):

    if current_user.role != "admin" and current_user.id != seller_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this seller"
        )
    
    seller = db.query(User).filter(User.id == seller_id, User.role == "seller").first()

    if not seller:
        raise HTTPException(
            status_code=404,
            detail="Seller not found"
        )
    
    return seller

@router.patch("/{seller_id}/status", response_model=SellerResponse)
def update_seller_status(
    seller_id: int,
    status: str,  # values: "approved" | "rejected" | "pending"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update seller status"
        )
    
    seller = db.query(User).filter(User.id == seller_id, User.role == "seller").first()

    if not seller:
        raise HTTPException(
            status_code=404,
            detail="Seller not found"
        )
    
    if status == "approved":
        seller.is_active = True
        seller.is_blocked = False

    elif status == "rejected":
        seller.is_active = False
        seller.is_blocked = True

    elif status == "pending":
        seller.is_active = False
        seller.is_blocked = False

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid status value"
        )
    
    db.commit()
    db.refresh(seller)
    return seller