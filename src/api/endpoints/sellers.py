from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    HTTPException,
    status,
    File,
    Form,
    UploadFile,
)
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from src.core.database import SessionLocal
from src.models.users import User 
from src.models.products import Product
from src.schemas.users import SellerCreate, SellerUpdate, SellerResponse
from src.schemas.products import ProductCreate
from src.utils.auth import get_current_active_user
from src.services.seller_service import SellerService, ProductService

router = APIRouter(prefix="/sellers", tags=["Sellers"])

# ----------------- Database Dependency -----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------- SELLER ACCOUNT MANAGEMENT -----------------
@router.get("/")
def get_sellers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all sellers (Admin only)."""
    return SellerService.get_all_sellers(db, current_user)


@router.post("/register", response_model=SellerResponse)
def register_seller(
    seller: SellerCreate,
    db: Session = Depends(get_db),
):
    """Register a new seller account."""
    return SellerService.register_seller(db, seller)


@router.get("/{seller_id}", response_model=SellerResponse)
def get_seller_by_id(
    seller_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get seller details by ID."""
    return SellerService.get_seller_by_id(db, seller_id, current_user)


@router.patch("/{seller_id}", response_model=SellerResponse)
async def update_seller(
    seller_id: int,
    seller_update: SellerUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update seller profile."""
    return await SellerService.update_seller(
        db, seller_id, seller_update, current_user, background_tasks
    )


@router.patch("/{seller_id}/status", response_model=SellerResponse)
def update_seller_status(
    seller_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Change seller active/inactive status."""
    return SellerService.update_seller_status(db, seller_id, status, current_user)


# ----------------- SELLER PRODUCT MANAGEMENT -----------------
@router.post("/products", response_model=ProductCreate)
def add_product(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    stock: int = Form(...),
    category_id: int = Form(...),
    images: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Add a new product (Seller only, supports multipart form-data).
    """

    # Ensure only sellers can add products
    if current_user.role != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add products",
        )

    # ✅ Delegate to service layer (handles file saving + DB)
    return ProductService.add_product(
        db=db,
        name=name,
        description=description,
        price=price,
        stock=stock,
        category_id=category_id,
        images=images,
        current_user=current_user,
    )
 

@router.put("/products/{prod_id}/update")
def update_product(
    prod_id: int,
    product_update: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update existing product (Seller only)."""
    return ProductService.update_product(
        db, current_user.id, prod_id, product_update, current_user
    )


@router.delete("/products/{prod_id}/delete")
def delete_product(
    prod_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a product (Seller only)."""
    return ProductService.delete_product(db, current_user.id, prod_id, current_user)


@router.get("/products/all")
def get_all_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """View all products added by the logged-in seller."""
    return ProductService.get_all_products(db, current_user.id, current_user)
