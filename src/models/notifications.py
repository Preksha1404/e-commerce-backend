from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from src.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer,ForeignKey("users.id"), index=True, nullable=False)
    order_id = Column(Integer, index=True, nullable=True)
    type = Column(String, nullable=False)                      # e.g. "new_order"
    payload = Column(JSON, nullable=True)                      # additional data (order total, items)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    seller = relationship("src.models.users.User", back_populates="notifications")
