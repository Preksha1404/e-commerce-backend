from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from src.models.coupons import DiscountType
from src.schemas.cart import CartItemOut

class CouponBase(BaseModel):
    coupon_name: str = Field(...)
    coupon_description: Optional[str] = Field(None, max_length=255)
    discount_type: DiscountType = Field(...)
    discount_value: float = Field(...)
    minimum_value: float = Field(0, ge=0)
    expiry_date: datetime = Field(...)
    usage_limit: int = Field(default=1, ge=1)

class CouponCreate(CouponBase):
    pass

class CouponUpdate(BaseModel):
    coupon_name: Optional[str]
    coupon_description: Optional[str]
    discount_type: Optional[DiscountType]
    discount_value: Optional[float]
    minimum_value: Optional[float]
    expiry_date: Optional[datetime]
    coupon_status: Optional[bool]
    usage_limit: Optional[int]

class CouponResponse(CouponBase):
    id: int
    user_id: int
    coupon_code: str
    used_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ApplyCouponRequest(BaseModel):
    coupon_code: str = Field(..., description="Coupon code to apply")

class ApplyCouponResponse(BaseModel):
    coupon_code: str
    valid: bool
    message: str
    discount_amount: float = 0.0
    final_price: float = 0.0
    items: List[CartItemOut] = []