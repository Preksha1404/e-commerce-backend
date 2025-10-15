from fastapi import APIRouter, Depends, HTTPException, Response, status, Cookie
from fastapi.responses import JSONResponse
import jwt
from sqlalchemy.orm import Session
from datetime import timedelta
from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import UserLogin, UserResponse
from src.utils.functions import verify_pwd, create_access_token, create_refresh_token,ACCESS_TOKEN_EXPIRE, REFRESH_TOKEN_EXPIRE
from src.utils.auth import get_current_active_user
from dotenv import load_dotenv
import os

router = APIRouter(prefix="/auth", tags=["Auth"])

load_dotenv()

SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login(
    credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
    ):

    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_pwd(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Only allow customer and seller roles
    if user.role not in ["customer", "seller"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to login here"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE)
    refresh_token = create_refresh_token(
        data={"sub": user.email},
        expires_delta=refresh_token_expires
    )
    
    user.refresh_token = refresh_token
    db.commit()

    # Create response with user data
    content = {
        "user": UserResponse.model_validate(user).model_dump(),
        "message": "Login successful"
    }
    
    # Create JSONResponse to set cookies
    response = JSONResponse(content=content)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=ACCESS_TOKEN_EXPIRE * 60
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=REFRESH_TOKEN_EXPIRE * 24 * 60 * 60
    )

    return response

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.post("/refresh")
def refresh_token(
    response: Response,
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(User).filter(User.email == email).first()
    if not user or user.refresh_token != refresh_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token({"sub": user.email})

    response.set_cookie("access_token", new_access_token, httponly=True)

    return {"access_token": new_access_token, "token_type": "bearer"}