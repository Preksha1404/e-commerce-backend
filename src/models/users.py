from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from src.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SELLER = "seller"
    CUSTOMER = "customer"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True} 
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    store_name = Column(String, nullable=True)
    store_address = Column(String, nullable=True)
    store_description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    profile_picture = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
 
    products = relationship("src.models.products.Product", back_populates="seller", lazy="dynamic")
    orders = relationship("src.models.orders.Order", back_populates="user", cascade="all, delete-orphan")
    carts = relationship("Cart", back_populates="user", cascade="all, delete-orphan")
    addresses = relationship("src.models.addresses.Address", back_populates="user", cascade="all, delete-orphan")
    
     
    coupons = relationship("Coupon", back_populates="user", cascade="all, delete-orphan")

 

