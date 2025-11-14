from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from src.core.database import Base


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    user_id = Column(Integer, nullable=True)

    rating = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ⭐ Back relation to Product
    product = relationship("Product", back_populates="ratings")
