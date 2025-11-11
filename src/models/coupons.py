from sqlalchemy import Table, Column, Integer, String, Float, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from src.core.database import Base

class DiscountType(enum.Enum):
    flat = "flat"
    percentage = "percentage"

class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    coupon_name = Column(String(100), nullable=False)
    coupon_description = Column(String(255), nullable=True)
    coupon_code = Column(String(50), unique=True, nullable=False)
    discount_type = Column(Enum(DiscountType), nullable=False)
    discount_value = Column(Float, nullable=False)
    minimum_value = Column(Float, default=0)
    expiry_date = Column(DateTime, nullable=False)
    coupon_status = Column(Boolean, default=True)
    usage_limit = Column(Integer, default=1)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Owner of coupon
    user = relationship("User", back_populates="coupons")  # Relationship with User

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
