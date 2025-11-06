from fastapi import Depends, HTTPException, status, Cookie, Header
from sqlalchemy.orm import Session
from typing import Optional
from src.models.users import User
from src.core.database import get_db
from src.schemas.users import UserRole
from src.utils.functions import verify_token

# Auth Dependencies
def get_current_user(
    access_token: Optional[str] = Cookie(None, include_in_schema=False),
    authorization: Optional[str] = Header(None, include_in_schema=False),  # hide from Swagger
    db: Session = Depends(get_db)
):
    # Use Authorization header if available, else fallback to cookie
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    token_data = verify_token(token)

    # Get user from DB
    user = db.query(User).filter(User.email == token_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensures the user is active.
    Already validated in get_current_user, so just returns the user.
    """
    return current_user

def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Allows access only if the user is an admin.
    """
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required."
        )
    return current_user

def require_roles(*allowed_roles: UserRole):
    """
    Allows access only if current_user.role is in allowed_roles.
    Usage: Depends(require_roles(UserRole.ADMIN, UserRole.SELLER))
    """
    def _require(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return _require
