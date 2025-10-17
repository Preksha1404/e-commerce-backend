from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import UserCreate, UserResponse
from src.utils.functions import get_pwd_hash
from src.utils.auth import get_current_active_user
from fastapi.responses import JSONResponse

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
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view all users"
        )
    users = db.query(User).filter(User.role == "customer").all()
    return users

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):

    # Check if email already exists
    if db.query(User).filter(User.email == user.email).first():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "error",
                "message": "Email already exists"
            }
        )
    
    hashed_password = get_pwd_hash(user.password)
    
    new_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        phone=user.phone,
        role="customer",
        is_active=True,
        is_blocked=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user