from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from src.models.orders import Order, OrderItem, OrderStatus, PaymentStatus
from src.models.products import Product
from src.models.addresses import Address
from src.models.users import User
from src.schemas.orders import OrderCreateSchema, OrderResponseSchema
from typing import List
from src.utils.order_status import update_order_overall_status
from src.services.product_service import ProductService
from src.services.email_service import send_email
from src.utils.email_templates import send_order_cancelled_email

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

    def place_order(self, order_data: OrderCreateSchema, current_user: User) -> OrderResponseSchema:
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
            if not product.is_active:
                raise HTTPException(status_code=400, detail=f"Product ID {product.name} is inactive")
            if product.is_deleted:
                raise HTTPException(status_code=400, detail=f"Product ID {product.name} is deleted")
            if product.stock < item.quantity:
                raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name}")

            unit_price = product.price
            total_price = unit_price * item.quantity
            total_amount += total_price

            order_items.append(
                OrderItem(
                    product_id=item.product_id,
                    seller_id=product.seller_id,
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

    async def cancel_order(self, order_id: int, current_user: User, background_tasks=BackgroundTasks):
        if current_user.role != "customer":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        order = self.db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == current_user.id
        ).first()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise HTTPException(status_code=400, detail="Cannot cancel shipped or delivered order")

        if order.status == OrderStatus.CANCELLED:
            raise HTTPException(status_code=400, detail="Order is already cancelled")

        # Update order status
        order.status = OrderStatus.CANCELLED

        # Restore product stock
        order_items = self.db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        for item in order_items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock += item.quantity  # increase stock

        self.db.commit()
        self.db.refresh(order)

        # Generate email content
        email_data = send_order_cancelled_email(
            user_email=current_user.email, 
            user_name=current_user.full_name, 
            order_id=order.id
        )

        # Send email asynchronously via background task
        await send_email(
            background_tasks,
            to_email=current_user.email,
            subject=email_data["subject"],
            html_content=email_data["html_content"]
        )

        return {
            "order_id": order.id,
            "status": order.status,
            "message": "Order cancelled successfully, stock restored",
        }

    # ---------------- Admin Method ---------------- #
    def get_all_orders(self, current_user: User) -> List[Order]:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")

        return self.db.query(Order).order_by(Order.created_at.desc()).all()
    
    # ---------------- Seller Methods ---------------- #
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
                    product = self.db.query(Product).filter(Product.id == item.product_id).first()
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
                product = self.db.query(Product).filter(Product.id == item.product_id).first()
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

        # Restrict invalid transitions
        if order_item.status in ["shipped", "delivered"] and new_status == "pending":
            raise HTTPException(status_code=400, detail="Cannot change status from shipped/delivered to pending")

        if order_item.status == "delivered" and new_status == "shipped":
            raise HTTPException(status_code=400, detail="Cannot change status from delivered to shipped")

        # Update valid status
        order_item.status = new_status
        self.db.commit()

        updated_order = update_order_overall_status(order_id, self.db)
        return updated_order