from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False) 
    name = Column(String, nullable=False)   
    rating = Column(Float, nullable=False)  
    comment = Column(String, nullable=False) 

    product = relationship("Product", back_populates="reviews")