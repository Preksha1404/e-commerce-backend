from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)  # linked to Product table
    name = Column(String, nullable=False)   # reviewer's name
    rating = Column(Float, nullable=False)  # rating out of 5
    comment = Column(String, nullable=False) # review comment

    product = relationship("Product", back_populates="reviews")
