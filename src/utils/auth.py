from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.orm import Session
from src.models.users import User
from src.utils.functions import verify_token
from src.core.database import get_db
from src.schemas.users import UserRole,UserResponse
from typing import Optional

# Auth Dependencies
def get_current_user(
    access_token: Optional[str] = Cookie(None, include_in_schema=False),
    db: Session = Depends(get_db)
):
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = verify_token(access_token)
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(
            status_code=404,
            detail="Inactive User",
        )
    return current_user

async def get_user_from_ws_token(token: str, db: Session):
    token_data = verify_token(token)
    return db.query(User).filter(User.email == token_data.email).first()

def require_admin(current_user: User = Depends(get_current_active_user)):
    """
    ✅ Dependency: Only allows access if the current user is an admin.
    """
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required."
        )
    return current_user

def require_roles(*allowed_roles: UserRole):
    def _require(current_user: UserResponse = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return _require
