from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.user import User
from src.schemas.users import UserLogin, UserResponse
from src.utils.functions import verify_pwd, create_access_token, ACCESS_TOKEN_EXPIRE
from datetime import timedelta

router = APIRouter(prefix="/admin", tags=["Admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Admin Login
@router.post("/login") 
def admin_login(credentials: UserLogin,
    db: Session = Depends(get_db),
    response: Response = None):
    
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_pwd(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Only allow admin role
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive admin account"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=ACCESS_TOKEN_EXPIRE
    )

    return {
        "user": UserResponse.model_validate(user)
    }

@router.post("/logout", response_model=dict)
def admin_logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}