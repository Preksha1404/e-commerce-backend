from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
)
from sqlalchemy.orm import Session
 
from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import (
    SellerCreate,
    SellerUpdate,
    SellerResponse,
)
from src.utils.auth import get_current_active_user
from src.services.seller_service import SellerService
from src.services.email_service import send_email
from src.utils.email_templates import user_block_status_template

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
async def update_seller_status(
    seller_id: int,
    status: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """🔹 Change seller active/inactive status."""
    return await SellerService.update_seller_status(db, seller_id, status, current_user, background_tasks)
 

@router.patch("/{seller_id}/toggle-block")
async def toggle_seller_block(
    seller_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Toggle (block/unblock) a seller — Admin-only access.
    Sends an email notification after the action.
    """

    # Toggle block/unblock using service
    seller = SellerService.toggle_seller_block(seller_id, db, current_user)

    # Template (re-using customer template)
    subject, html_content = user_block_status_template(
        full_name=seller.full_name or seller.username or "Seller",
        is_blocked=seller.is_blocked
    )

    # Send email
    await send_email(
        background_tasks=background_tasks,
        to_email=seller.email,
        subject=subject,
        html_content=html_content
    )

    return {
        "id": seller.id,
        "email": seller.email,
        "is_blocked": seller.is_blocked,
        "message": f"Seller has been {'blocked' if seller.is_blocked else 'unblocked'} and notified via email."
    }
