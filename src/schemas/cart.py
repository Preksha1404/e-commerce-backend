from pydantic import BaseModel, Field
from typing import List, Optional


class AddItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class UpdateItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(ge=0)


class ApplyCouponRequest(BaseModel):
    code: str


class CartItemOut(BaseModel):
    product_id: int
    name: str
    unit_price: float
    quantity: int
    line_total: float
    image_url: Optional[str] = None


class CartOut(BaseModel):
    items: List[CartItemOut] = Field(default_factory=list)
    subtotal: float
    discount: float
    total: float
    coupon: Optional[str] = None


class MessageResponse(BaseModel):
    message: str


class AddItemResponse(BaseModel):
    message: str
    items: List[CartItemOut] = Field(default_factory=list)
    subtotal: float
    discount: float
    total: float
    coupon: Optional[str] = None


class UpdateItemResponse(BaseModel):
    message: str
    items: List[CartItemOut] = Field(default_factory=list)
    subtotal: float
    discount: float
    total: float
    coupon: Optional[str] = None


class RemoveItemResponse(BaseModel):
    message: str
    items: List[CartItemOut] = Field(default_factory=list)
    subtotal: float
    discount: float
    total: float
    coupon: Optional[str] = None