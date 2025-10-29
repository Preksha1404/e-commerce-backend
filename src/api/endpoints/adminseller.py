from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models.user import User, UserRole
from src.core.database import get_db

router = APIRouter(prefix="/adminseller", tags=["Admin - Seller Control"])


 
@router.put("/activate-seller/{seller_id}")
def activate_seller(seller_id: int, db: Session = Depends(get_db)):
    seller = db.query(User).filter(User.id == seller_id, User.role == UserRole.SELLER).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.is_active = True
    db.commit()
    db.refresh(seller)
    return {"message": f"Seller {seller.full_name or seller.email} activated successfully"}

 
@router.put("/deactivate-seller/{seller_id}")
def deactivate_seller(seller_id: int, db: Session = Depends(get_db)):
    seller = db.query(User).filter(User.id == seller_id, User.role == UserRole.SELLER).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.is_active = False
    db.commit()
    db.refresh(seller)
    return {"message": f"Seller {seller.full_name or seller.email} deactivated successfully"}


 
@router.put("/block-seller/{seller_id}")
def block_seller(seller_id: int, db: Session = Depends(get_db)):
    seller = db.query(User).filter(User.id == seller_id, User.role == UserRole.SELLER).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.is_blocked = True
    seller.is_active = False  # optional: deactivate when blocked
    db.commit()
    db.refresh(seller)
    return {"message": f"Seller {seller.full_name or seller.email} has been blocked"}


 
@router.put("/unblock-seller/{seller_id}")
def unblock_seller(seller_id: int, db: Session = Depends(get_db)):
    seller = db.query(User).filter(User.id == seller_id, User.role == UserRole.SELLER).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.is_blocked = False
    db.commit()
    db.refresh(seller)
    return {"message": f"Seller {seller.full_name or seller.email} has been unblocked"}


 
@router.delete("/delete-seller/{seller_id}")
def delete_seller(seller_id: int, db: Session = Depends(get_db)):
    seller = db.query(User).filter(User.id == seller_id, User.role == UserRole.SELLER).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    db.delete(seller)
    db.commit()
    return {"message": f"Seller {seller.full_name or seller.email} deleted successfully"}

 
@router.get("/sellers")
def get_all_sellers(db: Session = Depends(get_db)):
    sellers = db.query(User).filter(User.role == UserRole.SELLER).all()
    return [
        {
            "id": s.id,
            "full_name": s.full_name,
            "email": s.email,
            "is_active": s.is_active,
            "is_blocked": s.is_blocked,
            "created_at": s.created_at,
        }
        for s in sellers
    ]
