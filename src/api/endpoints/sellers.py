from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import SellerCreate, SellerUpdate, SellerResponse
from src.schemas.products import ProductCreate
from src.utils.auth import get_current_active_user
from src.services.seller_service import SellerService

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
    current_user: User = Depends(get_current_active_user)
):
    """Get all sellers (Admin only)."""
    return SellerService.get_all_sellers(db, current_user)


@router.post("/register", response_model=SellerResponse)
def register_seller(
    seller: SellerCreate,
    db: Session = Depends(get_db)
):
    """Register a new seller account."""
    return SellerService.register_seller(db, seller)


@router.get("/{seller_id}", response_model=SellerResponse)
def get_seller_by_id(
    seller_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get seller details by ID."""
    return SellerService.get_seller_by_id(db, seller_id, current_user)


@router.patch("/{seller_id}", response_model=SellerResponse)
async def update_seller(
    seller_id: int,
    seller_update: SellerUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
):
    """Change seller active/inactive status."""
    return SellerService.update_seller_status(db, seller_id, status, current_user)


# ----------------- SELLER CONTROL APIs (PRODUCT MANAGEMENT) -----------------

@router.post("/{seller_id}/add")
def add_product(
    seller_id: int,
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a new product."""
    return SellerService.add_product(db, seller_id, product, current_user)


@router.put("/{seller_id}/{prod_id}/update")
def update_product(
    seller_id: int,
    prod_id: int,
    product_update: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update existing product details."""
    return SellerService.update_product(db, seller_id, prod_id, product_update, current_user)


@router.delete("/{seller_id}/{prod_id}/delete")
def delete_product(
    seller_id: int,
    prod_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a product."""
    return SellerService.delete_product(db, seller_id, prod_id, current_user)


@router.get("/{seller_id}/allProd")
def get_all_products(
    seller_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """View all products added by the seller."""
    return SellerService.get_all_products(db, seller_id, current_user)
