from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pyd import BaseModel, EmailStr
from src.core.database import get_db
from src.models.user import User, UserRole
from src.core.jwt import create_access_token
from src.core.dependencies import get_current_user
from src.utils.security import hash_password, verify_password
from src.utils.email import send_reset_email


router = APIRouter(prefix="/api/auth", tags=["Auth"])

# -------- Pydantic models --------
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    role: UserRole = UserRole.CUSTOMER

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# -------- Router & password context --------
router = APIRouter(prefix="/api/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------- Signup route --------
@router.post("/signup")
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # Extract fields from request
    email = request.email
    password = request.password
    full_name = request.full_name
    role = request.role

    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_pw = hash_password(password)

    # Create new user
    new_user = User(
        email=email,
        hashed_password=hashed_pw,
        full_name=full_name,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"msg": "User created successfully", "user_id": new_user.id}


# -------- Login route --------
@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401   token = create_access_token({"user_id": user.id, "role": user.role.value})
    return {"access_token": token, "token_type": "bearer"}


# -------- Logout route --------
@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # JWT logout is handled client-side
    return {"message": f"User {current_user.email} logged out"}
, detail="Invalid credentials")

    # Generate JWT
 