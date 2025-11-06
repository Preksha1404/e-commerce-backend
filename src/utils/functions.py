from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, status
import os
from dotenv import load_dotenv
from src.schemas.users import TokenData
import secrets
import hashlib
import random
import string
from jose import JWTError

load_dotenv()

SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE"))
REFRESH_TOKEN_EXPIRE = int(os.getenv("REFRESH_TOKEN_EXPIRE"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_pwd_hash(password: str) -> str:
    """
    Hash the password using bcrypt.
    Bcrypt automatically handles salting internally.
    """
    # bcrypt has 72-byte input limit, so truncate safely
    return pwd_context.hash(password[:72])

def verify_pwd(plain_pwd: str, hashed_pwd: str) -> bool:
    """
    Verify that a plain password matches its hashed version.
    """
    try:
        return pwd_context.verify(plain_pwd[:72], hashed_pwd)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()  # e.g., {"id": user.id, "email": user.email, "role": user.role}

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
    
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire=datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not verify credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        email: str = payload.get("email")
        role: str = payload.get("role")

        if email is None or user_id is None:
            raise credentials_exception

        return TokenData(id=user_id, email=email, role=role)

    except JWTError:
        raise credentials_exception
    
def generate_reset_token() -> str:
    return secrets.token_urlsafe(32) # Generate a secure random token

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest() # Hash the token using SHA-256

def generate_slug(text: str) -> str:
    """Generate a URL-friendly slug from text"""
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip().replace(' ', '-')
    # Remove special characters
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    # Remove multiple consecutive hyphens
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug

from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, status
import os
from dotenv import load_dotenv
from src.schemas.users import TokenData
import secrets
import hashlib
import random
import string
from jose import JWTError

load_dotenv()

SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE"))
REFRESH_TOKEN_EXPIRE = int(os.getenv("REFRESH_TOKEN_EXPIRE"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_pwd(plain_pwd: str, hashed_pwd: str) -> bool:
    return pwd_context.verify(plain_pwd[:72], hashed_pwd)

def get_pwd_hash(password:str) -> str:
    return pwd_context.hash(password[:72])

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()  # e.g., {"id": user.id, "email": user.email, "role": user.role}

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
    
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire=datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not verify credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("Decoded payload:", payload)  # Debug info

        user_id = payload.get("id")
        email = payload.get("sub")
        role = payload.get("role")

        if not user_id or not email:
            print("Missing id or email in token")
            raise credentials_exception

        # Optional: check expiration manually
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            print("Token expired")
            raise credentials_exception

        return TokenData(id=user_id, email=email, role=role)

    except JWTError as e:
        print("JWTError:", e)
        raise credentials_exception
def generate_reset_token() -> str:
    return secrets.token_urlsafe(32) # Generate a secure random token

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest() # Hash the token using SHA-256

def generate_slug(text: str) -> str:
    """Generate a URL-friendly slug from text"""
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip().replace(' ', '-')
    # Remove special characters
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    # Remove multiple consecutive hyphens
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug

def generate_simple_sku(name: str) -> str:
    """Generate a short SKU like PREFIX-001 from the product name.

    """
    # Normalize name and extract words
    words = name.strip().split()
    cleaned_words = [''.join(ch for ch in w if ch.isalnum()) for w in words]
    initials = ''.join(w[0] for w in cleaned_words if w)

    # If we couldn't get enough initials, fall back to first alnum chars in full name
    if len(initials) < 3:
        alnum_name = ''.join(ch for ch in name if ch.isalnum())
        initials = (initials + alnum_name)[:3]

    prefix = (initials[:3] or 'PRD').upper()
    number = random.randint(1, 999)
    return f"{prefix}-{number:03d}"