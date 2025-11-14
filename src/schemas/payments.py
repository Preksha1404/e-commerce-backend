from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from src.models.payment import PaymentStatus


class PaymentIntentCreate(BaseModel):
    order_id: int
    currency: Optional[str] = Field(default="usd", description="Currency code (e.g., 'usd')")
    metadata: Optional[Dict[str, Any]] = None


class PaymentIntentResponse(BaseModel):
    payment_intent_id: str
    client_secret: str
    amount: float
    currency: str
    status: str
    order_id: int

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    stripe_payment_intent_id: str
    stripe_charge_id: Optional[str]
    amount: float
    currency: str
    status: PaymentStatus
    payment_method: Optional[str]
    payment_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaymentConfirmRequest(BaseModel):
    payment_intent_id: str


class PaymentConfirmResponse(BaseModel):
    success: bool
    message: str
    payment: Optional[PaymentResponse] = None





class WebhookEvent(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]



