# Seller --> 
# /orders [GET] - Get all orders for the seller with only their items
# /orders/{order_id} [GET] - Get details of a specific order (only seller's products)
# /orders/{order_id}/items/{item_id}/status [PATCH] - Update status of a specific order item

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.orders import Order, OrderItem, OrderStatus
from src.schemas.orders import OrderResponseSchema, OrderSellerResponseSchema
from src.models.users import User
from src.utils.auth import get_current_active_user
from src.utils.order_status import update_order_overall_status
from typing import List

router = APIRouter(prefix="/seller", tags=["Seller Orders"])

# Get all orders for the seller with only their items
@router.get("/orders", response_model=List[OrderSellerResponseSchema])
def get_seller_orders(current_user: User = Depends(get_current_active_user),
                      db: Session = Depends(get_db)):
    if current_user.role != "seller":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    orders = db.query(Order).join(OrderItem).filter(OrderItem.seller_id == current_user.id).all()

    # For each order, include only items belonging to this seller
    seller_orders = []
    for order in orders:
        seller_items = [item for item in order.items if item.seller_id == current_user.id]
        order_data = {
            "id": order.id,
            "user_id": order.user_id,
            "total_amount": order.total_amount,
            "status": order.status,
            "created_at": order.created_at,
            "items": seller_items,  # only seller items
        }
        seller_orders.append(order_data)

    return seller_orders

# Get details of a specific order (only seller's products)
@router.get("/orders/{order_id}", response_model=OrderSellerResponseSchema)
def get_seller_order_details(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )

    # Fetch order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Fetch only items belonging to this seller
    seller_items = [item for item in order.items if item.seller_id == current_user.id]

    if not seller_items:
        raise HTTPException(
            status_code=403,
            detail="This order does not contain your products"
        )

    # Return only relevant details + seller-specific items
    order_data = {
        "id": order.id,
        "user_id": order.user_id,
        "total_amount": order.total_amount,
        "status": order.status,
        "created_at": order.created_at,
        "items": seller_items,
    }

    return order_data

@router.patch("/{order_id}/items/{item_id}/status", response_model=OrderResponseSchema)
def update_order_item_status(
    order_id: int,
    item_id: int,
    new_status: OrderStatus,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can update item status")

    # Check if the item belongs to this seller
    order_item = db.query(OrderItem).filter(
        OrderItem.id == item_id,
        OrderItem.order_id == order_id,
        OrderItem.seller_id == current_user.id
    ).first()

    if not order_item:
        raise HTTPException(status_code=404, detail="Item not found for this seller in this order")

    # Update the status of this specific item
    order_item.status = new_status
    db.commit()

    # Update overall order status after one item changes
    updated_order = update_order_overall_status(order_id, db)

    return updated_order