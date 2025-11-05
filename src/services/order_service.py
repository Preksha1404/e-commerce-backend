from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.models.orders import Order, OrderItem, OrderStatus, PaymentStatus
from src.models.products import Product
from src.models.addresses import Address
from src.models.users import User
from src.schemas.orders import OrderCreateSchema
from typing import List
from src.utils.order_status import update_order_overall_status
from src.services.product_service import ProductService

class OrderService:
    def __init__(self, db: Session):
        self.db = db

    # ---------------- User Methods ---------------- #

    def get_user_orders(self, current_user: User) -> List[Order]:
        if current_user.role != "customer":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
        return (
            self.db.query(Order)
            .filter(Order.user_id == current_user.id)
            .order_by(Order.created_at.desc())
            .all()
        )

    def place_order(self, order_data: OrderCreateSchema, current_user: User) -> Order:
        # Validate address
        address = self.db.query(Address).filter(
            Address.id == order_data.address_id,
            Address.user_id == current_user.id
        ).first()
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")

        # Prepare order items and calculate total
        total_amount = 0
        order_items = []
        for item in order_data.items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")
            if product.stock < item.quantity:
                raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name}")

            unit_price = product.price
            total_price = unit_price * item.quantity
            total_amount += total_price

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
            address_id=address.id,
            payment_method=order_data.payment_method,
            total_amount=total_amount,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.FAILED,
        )
        self.db.add(order)
        self.db.flush()  # Get order.id

        # Add order items & update stock
        for oi in order_items:
            oi.order_id = order.id
            self.db.add(oi)
            product = self.db.query(Product).filter(Product.id == oi.product_id).first()
            product.stock -= oi.quantity

        self.db.commit()
        self.db.refresh(order)
        return order

    def cancel_order(self, order_id: int, current_user: User):
        if current_user.role != "customer":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        order = self.db.query(Order).filter(
            Order.id == order_id, Order.user_id == current_user.id
        ).first()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise HTTPException(status_code=400, detail="Cannot cancel shipped or delivered order")
        if order.status == OrderStatus.CANCELLED:
            raise HTTPException(status_code=400, detail="Order is already cancelled")

        order.status = OrderStatus.CANCELLED
        self.db.commit()

        return {
            "order_id": order.id,
            "status": order.status,
            "message": "Order cancelled successfully",
        }

    # ---------------- Admin Method ---------------- #
    def get_seller_orders(self, current_user: User) -> List[dict]:
        if current_user.role != "seller":
            raise HTTPException(status_code=403, detail="Not authorized")

        orders = (
            self.db.query(Order)
            .join(OrderItem)
            .filter(OrderItem.seller_id == current_user.id)
            .all()
        )

        seller_orders = []
        for order in orders:
            seller_items = []
            for item in order.items:
                if item.seller_id == current_user.id:
                    # Fetch minimal product info
                    product = ProductService(self.db, None).get_product(item.product_id)
                    seller_items.append({
                        "id": item.id,
                        "product": {"name": product.name, "sku": product.sku},
                        "seller_id": item.seller_id,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "total_price": item.total_price,
                        "status": item.status
                    })

            seller_orders.append({
                "id": order.id,
                "user_id": order.user_id,
                "total_amount": order.total_amount,
                "status": order.status,
                "payment_status": order.payment_status,
                "created_at": order.created_at,
                "address": order.address,
                "items": seller_items
            })
        return seller_orders
    
    def get_seller_order_details(self, order_id: int, current_user: User) -> dict:
        if current_user.role != "seller":
            raise HTTPException(status_code=403, detail="Not authorized")

        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        seller_items = []
        for item in order.items:
            if item.seller_id == current_user.id:
                # Fetch minimal product info
                product = ProductService(self.db, None).get_product(item.product_id)
                seller_items.append({
                    "id": item.id,
                    "product": {
                        "name": product.name,
                        "sku": product.sku
                    },
                    "seller_id": item.seller_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "status": item.status
                })

        if not seller_items:
            raise HTTPException(status_code=403, detail="This order does not contain your products")

        return {
            "id": order.id,
            "user_id": order.user_id,
            "total_amount": order.total_amount,
            "status": order.status,
            "payment_status": order.payment_status,
            "created_at": order.created_at,
            "address": order.address,
            "items": seller_items
        }

    def update_order_item_status(self, order_id: int, item_id: int, new_status: OrderStatus, current_user: User):
        if current_user.role != "seller":
            raise HTTPException(status_code=403, detail="Only sellers can update item status")

        order_item = self.db.query(OrderItem).filter(
            OrderItem.id == item_id,
            OrderItem.order_id == order_id,
            OrderItem.seller_id == current_user.id,
        ).first()

        if not order_item:
            raise HTTPException(status_code=404, detail="Item not found for this seller in this order")

        order_item.status = new_status
        self.db.commit()

        updated_order = update_order_overall_status(order_id, self.db)
        return updated_order