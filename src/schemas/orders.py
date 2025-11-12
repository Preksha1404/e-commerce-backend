from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from src.models.orders import OrderStatus, PaymentStatus
from src.schemas.addresses import AddressOut
from src.schemas.products import ProductImageResponse

class OrderSellerProductInfo(BaseModel):
    name: str
    sku: str

    class Config:
        orm_mode = True

class OrderProductInfo(BaseModel):
    id: int
    name: str
    sku: str
    images: List[ProductImageResponse] = Field(default_factory=list)

    class Config:
        orm_mode = True

class OrderSellerItemSchema(BaseModel):
    id: int
    product: OrderSellerProductInfo
    seller_id: int
    quantity: int
    unit_price: float
    total_price: float
    status: OrderStatus

    class Config:
        orm_mode = True

class OrderItemSchema(BaseModel):
    id: int
    product: OrderProductInfo
    seller_id: int
    quantity: int
    unit_price: float
    total_price: float
    status: OrderStatus

    class Config:
        orm_mode = True

class OrderItemCreateSchema(BaseModel):
    product_id: int
    quantity: int

class OrderCreateSchema(BaseModel):
    address_id: int
    payment_method: str

class OrderResponseSchema(BaseModel):
    id: int
    user_id: int
    total_amount: float
    discount: float = 0.0
    subtotal: float = 0.0
    coupon_code: Optional[str] = None
    status: OrderStatus
    payment_status: PaymentStatus
    address: Optional[AddressOut]
    payment_method: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[OrderItemSchema]

    model_config = {
        "from_attributes": True
    }

class OrderCancelResponse(BaseModel):
    order_id: int
    status: OrderStatus
    message: str

class OrderSellerResponseSchema(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: OrderStatus
    payment_status: PaymentStatus
    created_at: datetime
    address: Optional[AddressOut]
    items: List[OrderSellerItemSchema]

    class Config:
        orm_mode = True

class OrderStatusUpdateSchema(BaseModel):
    new_status: OrderStatus