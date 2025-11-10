# User --> 
# /orders [GET] - Get all orders for a user
# /orders [POST] - Place a new order
# /orders/{order_id} [GET] - Get details of a specific order
# /orders/{order_id}/cancel [PATCH] - Cancel order (if not yet shipped

from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from src.core.database import get_db
from src.utils.auth import get_current_active_user
from src.models.users import User
from src.schemas.orders import OrderCreateSchema, OrderResponseSchema, OrderCancelResponse
from src.services.order_service import OrderService

router = APIRouter(prefix="/user", tags=["User Orders"])

@router.get("/orders", response_model=List[OrderResponseSchema])
def get_user_orders(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    return service.get_user_orders(current_user)

@router.post("/orders", response_model=OrderResponseSchema, status_code=status.HTTP_201_CREATED)
def place_order(
    order_data: OrderCreateSchema,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    return service.place_order(order_data, current_user)

@router.patch("/orders/{order_id}/cancel", response_model=OrderCancelResponse)
async def cancel_order(
    order_id: int,
    background_tasks:BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    return await service.cancel_order(order_id, current_user, background_tasks)