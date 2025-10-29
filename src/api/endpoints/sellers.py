from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import SellerCreate, SellerUpdate, SellerResponse
from src.utils.auth import get_current_active_user
from src.services.seller_service import SellerService

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
    return SellerService.get_all_sellers(db, current_user)

@router.post("/register", response_model=SellerResponse)
def register_seller(
    seller: SellerCreate,
    db: Session = Depends(get_db)
):
    return SellerService.register_seller(db, seller)

@router.get("/{seller_id}", response_model=SellerResponse)
def get_seller_by_id(
    seller_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return SellerService.get_seller_by_id(db, seller_id, current_user)

@router.patch("/{seller_id}", response_model=SellerResponse)
async def update_seller(
    seller_id: int,
    seller_update: SellerUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
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
    return SellerService.update_seller_status(db, seller_id, status, current_user)