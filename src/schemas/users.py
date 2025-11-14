from pydantic import BaseModel, EmailStr, Field
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional, List
from enum import Enum

# ----------------------------
# Enums
# ----------------------------
class UserRole(str, Enum):
    ADMIN = "admin"
    SELLER = "seller"
    CUSTOMER = "customer"

# ----------------------------  
# Input/Create Models
# ----------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: PhoneNumber

class SellerCreate(UserCreate):
    role: UserRole = Field(default=UserRole.SELLER)
    store_name: str
    store_address: str
    store_description: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[PhoneNumber] = None

class SellerUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[PhoneNumber] = None
    store_name: Optional[str] = None
    store_address: Optional[str] = None
    store_description: Optional[str] = None

# ----------------------------
# Core Models
# ----------------------------
class User(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    profile_picture: Optional[str] = None
    phone:PhoneNumber

# ----------------------------
# Response Models
# ----------------------------
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
    store_description: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class SellerSummaryResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_blocked: bool

    model_config = {
        "from_attributes": True
    }

class SellerBlockStatusResponse(SellerSummaryResponse):
    status: str
    message: str

    model_config = {
        "from_attributes": True
    }

# ----------------------------
# Auth‑related Models
# ----------------------------
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[int] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., alias="old_password")
    new_password: str = Field(..., alias="new_password")

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# ----------------------------
# Seller‑specific Request Models
# ----------------------------
class SellerBlockToggleRequest(BaseModel):
    is_blocked: bool
