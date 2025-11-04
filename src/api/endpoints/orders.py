# Admin --> 
# /admin/orders [GET] - Get all orders (admin only)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.orders import Order
from src.schemas.orders import OrderResponseSchema
from src.models.users import User
from src.utils.auth import get_current_active_user
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin Orders"])

# Get all orders
@router.get("/orders", response_model=List[OrderResponseSchema])
def get_all_orders(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this resource")

    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return orders