from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from src.models.orders import OrderStatus
from datetime import datetime

class OrderItemSchema(BaseModel):
    id: int
    product_id: int
    seller_id: int
    quantity: int
    unit_price: float
    total_price: float
    status: OrderStatus

    class Config:
        orm_mode = True

class OrderItemCreateSchema(BaseModel):
    product_id: int
    seller_id: int
    quantity: int

class OrderCreateSchema(BaseModel):
    shipping_address: str
    payment_method: str
    items: List[OrderItemCreateSchema]  # Each order_item contains product_id, quantity, unit_price, seller_id

class OrderResponseSchema(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: OrderStatus
    shipping_address: Optional[str]
    payment_method: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[OrderItemSchema]
    
    class Config:
        orm_mode = True

class OrderCancelResponse(BaseModel):
    order_id: int
    status: OrderStatus
    message: str

class OrderSellerResponseSchema(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemSchema]

    class Config:
        orm_mode = True