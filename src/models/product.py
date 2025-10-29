from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.core.database import Base
import enum

# 🟡 Step 1: Add product status enum
class ProductStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    discount_price = Column(Float, nullable=True)
    stock = Column(Integer, default=0)
    slug = Column(String, unique=True, nullable=False)
    sku = Column(String, unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 🟢 Add seller reference
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    status = Column(Enum(ProductStatus), default=ProductStatus.PENDING, nullable=False)  # 🟡 Approval field
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("Category", back_populates="products")
    seller = relationship("User")  # optional but helpful for joins
