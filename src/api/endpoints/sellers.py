from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    HTTPException,
    status,
    File,
    Form,
    UploadFile,
    Path,
)
from sqlalchemy.orm import Session
from typing import List, Optional

from src.core.database import SessionLocal
from src.models.users import User
from src.models.products import Product
from src.schemas.users import (
    SellerCreate,
    SellerUpdate,
    SellerResponse,
    SellerResponses,
)
from src.utils.auth import get_current_active_user, require_admin
from src.services.seller_service import SellerService, ProductService
from src.utils.email import send_seller_block_status_email, send_seller_verification_email,send_email
from src.services.invoice_generator import generate_pdf
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
    """🔹 Get all sellers (Admin only)."""
    return SellerService.get_all_sellers(db, current_user)


@router.post("/register", response_model=SellerResponse)
async def register_seller(
    seller: SellerCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """🔹 Register a new seller account."""
    return await SellerService.register_seller(db, seller, background_tasks)


@router.get("/{seller_id}", response_model=SellerResponse)
def get_seller_by_id(
    seller_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """🔹 Get seller details by ID."""
    return SellerService.get_seller_by_id(db, seller_id, current_user)


@router.patch("/{seller_id}", response_model=SellerResponse)
async def update_seller(
    seller_id: int,
    seller_update: SellerUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """🔹 Update seller profile."""
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
    """🔹 Change seller active/inactive status."""
    return SellerService.update_seller_status(db, seller_id, status, current_user)


# ----------------- BLOCK / UNBLOCK SELLER (Admin only) -----------------
@router.patch(
    "/{seller_id}/block-toggle",
    dependencies=[Depends(require_admin)],
    summary="Toggle block/unblock status for a seller (Admin only)",
)
async def toggle_seller_block_status(
    seller_id: int = Path(..., ge=1),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """🔒 Toggle block/unblock seller (Admin-only access)."""
    
    # --- Fetch seller ---
    seller = db.query(User).filter(User.id == seller_id, User.role == "seller").first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    # --- Toggle block status ---
    seller.is_blocked = not seller.is_blocked
    db.commit()
    db.refresh(seller)

    # --- Hide/show all old products ---
    db.query(Product).filter(Product.seller_id == seller.id).update(
        {"is_active": not seller.is_blocked},  # blocked → inactive, unblocked → active
        synchronize_session=False
    )
    db.commit()

    # --- Send async email ---
    await send_seller_block_status_email(
        email=seller.email,
        full_name=seller.full_name or seller.username or "Seller",
        is_blocked=seller.is_blocked,
        background_tasks=background_tasks
    )

    # --- Prepare response ---
    status_text = "blocked" if seller.is_blocked else "unblocked"
    return {
        "id": seller.id,
        "email": seller.email,
        "full_name": seller.full_name,
        "is_blocked": seller.is_blocked,
        "status": status_text,
        "message": f"Seller {seller.full_name} has been {status_text} successfully. "
                   "All their products are now " + ("hidden" if seller.is_blocked else "visible")
    }