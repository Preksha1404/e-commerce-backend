# Admin endpoint to get all orders

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from src.core.database import get_db
from src.models.users import User
from src.schemas.orders import OrderResponseSchema
from src.utils.auth import get_current_active_user
from src.services.order_service import OrderService

router = APIRouter(prefix="/admin", tags=["Admin Orders"])

@router.get("/orders", response_model=List[OrderResponseSchema])
def get_all_orders(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    return service.get_all_orders(current_user)