from http.client import HTTPException
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import UserCreate, UserUpdate, UserResponse
from src.utils.auth import get_current_active_user
from src.services.user_service import UserService
from src.utils.email import send_seller_block_status_email
from src.utils.email import send_customer_block_status_email
router = APIRouter(prefix="/users", tags=["Users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return UserService.get_all_users(db, current_user)

@router.post("/register", response_model=UserResponse)
async def register_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    return await UserService.register_user(db, user, background_tasks)

@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return UserService.update_user(db, user_id, user_update, current_user)
@router.patch("/{user_id}/toggle-block")
async def toggle_customer_block(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Toggle (block/unblock) a customer — Admin-only access.
    Sends email notification to the user after the action.
    """
    user = UserService.toggle_customer_block(user_id, db, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Send block/unblock email
    await send_customer_block_status_email(
        email=user.email,
        full_name=user.full_name or user.username or "Customer",
        is_blocked=user.is_blocked,
        background_tasks=background_tasks
    )

    return {
        "id": user.id,
        "email": user.email,
        "is_blocked": user.is_blocked,
        "message": f"User has been {'blocked' if user.is_blocked else 'unblocked'} and notified via email."
    }

