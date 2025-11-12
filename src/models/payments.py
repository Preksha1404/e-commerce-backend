from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.core.database import Base
import enum


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False, unique=True)
    stripe_payment_intent_id = Column(String, unique=True, nullable=False, index=True)
    stripe_charge_id = Column(String, nullable=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="usd", nullable=False)
    status = Column(Enum(PaymentStatus, native_enum=False, length=20), default=PaymentStatus.PENDING, nullable=False)
    payment_method = Column(String, nullable=True)
    payment_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    order = relationship("Order", backref="payment")



