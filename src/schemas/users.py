from pydantic import BaseModel, EmailStr, Field
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    SELLER = "seller"
    CUSTOMER = "customer"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: PhoneNumber

class SellerCreate(UserCreate):
    role: UserRole = Field(default=UserRole.SELLER)
    store_name: str
    store_address: str

class User(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    profile_picture: Optional[str] = None
    phone: PhoneNumber

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: Optional[PhoneNumber] = None
    role: UserRole
    profile_picture: Optional[str] = None
    is_active: bool
    is_blocked: bool
    
    model_config = {
        "from_attributes": True
    }

class SellerResponse(UserResponse):
    store_name: Optional[str] = None
    store_address: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: EmailStr | None = None

class ChangePasswordRequest(BaseModel):
    old_password: str=Field(...)
    new_password: str=Field(...)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str