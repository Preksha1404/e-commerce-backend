from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, status
import os
from dotenv import load_dotenv
from src.schemas.users import TokenData

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

def create_access_token(data:dict, expires_delta: Optional[timedelta]= None):
    to_encode = data.copy() # User data (email) to be encoded in the token
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
        
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY,algorithm=ALGORITHM) # Encode the token
    return encoded_jwt
    
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire=datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token:str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # Decode the token
        email: str = payload.get("sub") # subject --> jwt payload key
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not verify creditials",
                headers={"WWW-Authenticate":"Bearer"}
            )
        return TokenData(email=email) # Return the email in TokenData schema
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not verify creditials",
                headers={"WWW-Authenticate":"Bearer"}
        )