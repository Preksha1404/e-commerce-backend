# Seller --> 
# /orders [GET] - Get all orders for the seller with only their items
# /orders/{order_id} [GET] - Get details of a specific order (only seller's products)
# /orders/{order_id}/items/{item_id}/status [PATCH] - Update status of a specific order item

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from src.core.database import get_db
from src.models.users import User
from src.models.orders import OrderStatus
from src.schemas.orders import OrderResponseSchema, OrderSellerResponseSchema, OrderStatusUpdateSchema
from src.utils.auth import get_current_active_user
from src.services.order_service import OrderService

router = APIRouter(prefix="/seller", tags=["Seller Orders"])


@router.get("/orders", response_model=List[OrderSellerResponseSchema])
def get_seller_orders(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    return service.get_seller_orders(current_user)

@router.get("/orders/{order_id}", response_model=OrderSellerResponseSchema)
def get_seller_order_details(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    return service.get_seller_order_details(order_id, current_user)

@router.patch("/orders/{order_id}/items/{item_id}/status", response_model=OrderResponseSchema)
async def update_order_item_status(
    order_id: int,
    item_id: int,
    status_update: OrderStatusUpdateSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    return await service.update_order_item_status(
        order_id=order_id,
        item_id=item_id,
        new_status=status_update.new_status,
        current_user=current_user,
        background_tasks=background_tasks,
    )