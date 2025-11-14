from sqlalchemy import ( # type: ignore
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Enum
)
from sqlalchemy.sql import func # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from src.core.database import Base
import enum
 
from src.models.payment import Payment

# ===========================
# ENUMS
# ===========================

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    PAID = "paid"
    FAILED = "failed"


class OrderItemStatus(str, enum.Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# ===========================
# CART MODELS
# ===========================

class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=True)

    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    user = relationship("src.models.users.User", backref="carts")
    coupon = relationship("Coupon", backref="carts", lazy="joined")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")


# ===========================
# ORDER MODELS
# ===========================

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False)

    total_amount = Column(Float, default=0.0)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.FAILED)

    payment_method = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    # In Payment model
 
    # In Order model
    payments = relationship("Payment", back_populates="order", uselist=False)


    user = relationship("User", back_populates="orders")
    address = relationship("Address", back_populates="orders")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    status = Column(Enum(OrderItemStatus), default=OrderItemStatus.PENDING)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    seller = relationship("User", backref="order_items")



 