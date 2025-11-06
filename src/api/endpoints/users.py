from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import UserCreate, UserUpdate, UserResponse
from src.utils.auth import get_current_active_user
from src.services.user_service import UserService

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
def toggle_customer_block(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Toggle (block/unblock) a customer — Admin-only access.
    """
    return UserService.toggle_customer_block(user_id, db, current_user)
