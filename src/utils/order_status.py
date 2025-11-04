from sqlalchemy.orm import Session
from src.models.orders import Order, OrderItem, OrderStatus

def update_order_overall_status(order_id: int, db: Session):
    """
    Updates the overall order status based on its items' statuses.
    Logic:
      - If all items are DELIVERED → Order = DELIVERED
      - Else if any item is SHIPPED → Order = SHIPPED
      - Else if all items are CANCELLED → Order = CANCELLED
      - Else → Order = PENDING
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return None

    all_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    item_statuses = [item.status for item in all_items]

    if not item_statuses:
        return order  # no items case

    if all(s == OrderStatus.DELIVERED for s in item_statuses):
        order.status = OrderStatus.DELIVERED
    elif any(s == OrderStatus.SHIPPED for s in item_statuses):
        order.status = OrderStatus.SHIPPED
    elif all(s == OrderStatus.CANCELLED for s in item_statuses):
        order.status = OrderStatus.CANCELLED
    else:
        order.status = OrderStatus.PENDING

    db.commit()
    db.refresh(order)
    return order