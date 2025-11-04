# User --> 
# /orders [GET] - Get all orders for a user
# /orders [POST] - Place a new order
# /orders/{order_id} [GET] - Get details of a specific order
# /orders/{order_id}/cancel [PATCH] - Cancel order (if not yet shipped

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.orders import Order, OrderItem, OrderStatus
from src.models.products import Product
from src.schemas.orders import OrderCreateSchema, OrderResponseSchema, OrderCancelResponse
from src.models.users import User
from src.utils.auth import get_current_active_user
from typing import List

router = APIRouter(prefix="/user", tags=["User Orders"])

# Get all orders for a user
@router.get("/orders", response_model=List[OrderResponseSchema])
def get_user_orders(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "customer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this resource")
    
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return orders

# Place a new order
@router.post("/orders", response_model=OrderResponseSchema, status_code=status.HTTP_201_CREATED)
def place_order(
    order_data: OrderCreateSchema,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Validate products and calculate total
    total_amount = 0
    order_items = []

    for item in order_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")

        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name}")

        # Use current product.price as unit_price
        unit_price = product.price
        total_price = unit_price * item.quantity
        total_amount += total_price

        # Prepare order item
        order_items.append(
            OrderItem(
                product_id=item.product_id,
                seller_id=item.seller_id,
                quantity=item.quantity,
                unit_price=unit_price,
                total_price=total_price,
            )
        )

    # Create order
    order = Order(
        user_id=current_user.id,
        shipping_address=order_data.shipping_address,
        payment_method=order_data.payment_method,
        total_amount=total_amount,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    db.flush()  # To get order.id before committing

    # Assign order_id to order items and add them
    for oi in order_items:
        oi.order_id = order.id
        db.add(oi)

        # Reduce stock
        product = db.query(Product).filter(Product.id == oi.product_id).first()
        product.stock -= oi.quantity

    db.commit()
    db.refresh(order)
    return order

# Get details of a specific order
@router.get("/orders/{order_id}", response_model=OrderResponseSchema)
def get_order_details(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# Cancel order (if not yet shipped)
@router.patch("/orders/{order_id}/cancel", response_model=OrderCancelResponse)
def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
        raise HTTPException(
            status_code=400, detail="Cannot cancel shipped or delivered order"
        )

    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Order is already cancelled")
    
    order.status = OrderStatus.CANCELLED
    db.commit()
    return {
        "order_id": order.id,
        "status": order.status,
        "message": "Order cancelled successfully",
    }