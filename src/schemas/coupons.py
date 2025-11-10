from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from src.models.coupons import DiscountType

class CouponBase(BaseModel):
    coupon_name: str = Field(...)
    coupon_code: Optional[str] = Field(None)
    discount_type: DiscountType = Field(...)
    discount_value: float = Field(...)
    minimum_value: float = Field(0, ge=0)
    expiry_date: datetime = Field(...)
    coupon_status: bool = Field(default=True)
    usage_limit: int = Field(default=1, ge=1)

class CouponCreate(CouponBase):
    user_id: int  # Include creator's user_id

class CouponUpdate(BaseModel):
    coupon_name: Optional[str]
    discount_type: Optional[DiscountType]
    discount_value: Optional[float]
    minimum_value: Optional[float]
    expiry_date: Optional[datetime]
    coupon_status: Optional[bool]
    usage_limit: Optional[int]

class CouponResponse(CouponBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ApplyCouponRequest(BaseModel):
    coupon_code: str = Field(...)
    cart_total: float = Field(..., gt=0)

class ApplyCouponResponse(BaseModel):
    valid: bool
    message: str
    discount_amount: float = 0.0
    final_price: float = 0.0