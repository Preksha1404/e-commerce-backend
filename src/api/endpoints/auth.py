from fastapi import APIRouter, Depends, HTTPException, Response, status, Cookie, BackgroundTasks
from fastapi.responses import JSONResponse
import jwt
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from src.core.database import SessionLocal
from src.models.users import User
from src.schemas.users import UserLogin, UserResponse, ChangePasswordRequest,ForgotPasswordRequest, ResetPasswordRequest
from src.utils.functions import get_pwd_hash,verify_pwd, create_access_token, create_refresh_token,ACCESS_TOKEN_EXPIRE, REFRESH_TOKEN_EXPIRE, generate_reset_token, hash_token
from src.utils.auth import get_current_active_user
from dotenv import load_dotenv
import os
from src.utils.email import send_reset_email

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
    
    if user.role not in ["customer", "seller", "admin"]:
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
        samesite="None",
        secure=True,
        max_age=ACCESS_TOKEN_EXPIRE * 60
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="None",
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
    refresh_token: str = Cookie(...),
    db: Session = Depends(get_db),
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

@router.patch('/change-password', response_model=dict)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    user=db.query(User).filter(User.id==current_user.id).first()

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="Admin users cannot change their password")
    
    # Access request attributes correctly
    old_password = request.old_password
    new_password = request.new_password

    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="Old and new passwords are required")

    if not verify_pwd(old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    # Update password
    user.hashed_password = get_pwd_hash(new_password)
    
    db.commit()
    db.refresh(user)

    return {"message": "Password updated successfully"}

@router.post("/forget-password")
async def forget_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    ):
    """
    Step 1: Request password reset
    - Receives email
    - Generates token
    - Sends reset email
    """
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    reset_token = generate_reset_token()

    hashed_token = hash_token(reset_token)
    
    user.reset_token = hashed_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    # Send reset email in background
    await send_reset_email(request.email, reset_token, background_tasks)

    return {
        "message": "A reset link has been sent"
    }

@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
    ):
    """
    Step 2: Reset password with token
    - Validates token
    - Checks expiration
    - Updates password
    """
    
    # Hash the incoming token if you stored hashed tokens
    hashed_token = hash_token(request.token)
    
    # Find user by token
    user = db.query(User).filter(
        User.reset_token == hashed_token
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )
    
    # Check if token is expired
    if not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Reset token has expired"
        )

    # Update password
    user.hashed_password = get_pwd_hash(request.new_password)
    
    # Clear reset token fields
    user.reset_token = None
    user.reset_token_expires = None
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Password has been reset successfully",
    }

@router.post("/logout", response_model=dict)
def logout(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
    ):

    current_user.refresh_token = None
    db.commit()

    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return {"message": "Successfully logged out"}