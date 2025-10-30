from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.orm import Session
from src.models.users import User
from src.utils.functions import verify_token
from src.core.database import get_db

# Auth Dependencies
def get_current_user(
    access_token: str = Cookie(..., include_in_schema=False),
    db: Session = Depends(get_db)
):
    token_data = verify_token(access_token)
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(
            status_code=404,
            detail="Inactive User",
        )
    return current_user