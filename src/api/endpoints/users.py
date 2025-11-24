from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import UserCreate, UserUpdate, UserResponse
from src.utils.auth import get_current_active_user
from src.services.user_service import UserService
from src.services.email_service import send_email
from src.utils.email_templates import user_block_status_template, contact_us_email_template
from src.services.contact_service import ContactService
from src.schemas.contact import ContactRequest

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
    # Toggle block/unblock status
    user = UserService.toggle_customer_block(user_id, db, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate email subject & html content using template
    subject, html_content = user_block_status_template(
        full_name=user.full_name or user.username or "Customer",
        is_blocked=user.is_blocked
    )

    # Send email using generic send_email function
    await send_email(
        background_tasks=background_tasks,
        to_email=user.email,
        subject=subject,
        html_content=html_content
    )

    return {
        "id": user.id,
        "email": user.email,
        "is_blocked": user.is_blocked,
        "message": f"User has been {'blocked' if user.is_blocked else 'unblocked'} and notified via email."
    }

@router.post("/contact")
async def contact_us(
    form: ContactRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    return await ContactService.submit_contact_form(
        db=db,
        form=form,
        background_tasks=background_tasks
    )