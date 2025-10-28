from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.core.jwt import verify_token
from src.core.database import get_db
from src.models.user import User, UserRole
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    
    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active or user.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not allowed")
    
    return user

def admin_required(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access only")
    return current_user
