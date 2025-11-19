from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session, selectinload
from src.models.orders import Order, OrderItem, OrderStatus, PaymentStatus
from src.models.products import Product
from src.models.addresses import Address
from src.models.users import User
from src.schemas.orders import OrderCreateSchema, OrderResponseSchema
from typing import List
from src.utils.order_status import update_order_overall_status
from src.services.email_service import send_email
from src.utils.email_templates import send_order_cancelled_email
from src.services.cart_service import _serialize_cart, clear_cart, get_or_create_cart
from src.services.notification_service import NotificationService
from src.websockets.connection_manager import manager

class OrderService:
    def __init__(self, db: Session):
        self.db = db

    # ---------------- User Methods ---------------- #
    def get_user_orders(self, current_user: User) -> List[Order]:
        if current_user.role.value != "customer":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
        return (
            self.db.query(Order)
            .filter(Order.user_id == current_user.id)
            .order_by(Order.created_at.desc())
            .all()
        )

    async def place_order(self, order_data: OrderCreateSchema, current_user: User) -> OrderResponseSchema:
        # Validate address
        address = self.db.query(Address).filter(
            Address.id == order_data.address_id,
            Address.user_id == current_user.id
        ).first()
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")

        # Get user's active cart with applied coupon
        cart = get_or_create_cart(self.db, current_user.id)
        if not cart or not cart.items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        coupon = cart.coupon

        # Compute totals with coupon
        cart_out = _serialize_cart(self.db, cart, coupon=coupon)
        discount = cart_out.discount
        subtotal = cart_out.subtotal
        total_amount = cart_out.total

        # Prepare order items from cart
        order_items = []
        for item in cart_out.items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product ID {item.product_id} not found")
            if not product.is_active or product.is_deleted:
                raise HTTPException(status_code=400, detail=f"Product {product.name} is unavailable")
            if product.stock < item.quantity:
                raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")

            order_items.append(
                OrderItem(
                    product_id=item.product_id,
                    seller_id=product.seller_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.line_total,
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

            # STORE COUPON USAGE
            coupon_id=coupon.id if coupon else None,
            coupon_discount=discount if coupon else 0
        )

        self.db.add(order)
        self.db.flush()  # Get order.id

        # Add order items
        for oi in order_items:
            oi.order_id = order.id
            self.db.add(oi)

        # UPDATE COUPON USAGE COUNT ONLY AFTER ORDER CREATED
        if coupon:
            coupon.used_count += 1

        # Commit everything
        self.db.commit()

        # Clear cart AFTER coupon usage is saved
        clear_cart(self.db, current_user.id)

        self.db.refresh(order)

        # Build API response
        response = OrderResponseSchema.model_validate(order, from_attributes=True)
        response.discount = discount
        response.subtotal = subtotal
        response.coupon_code = coupon.coupon_code if coupon else None

        # Trigger Seller Notifications
        notif_service = NotificationService(self.db)
        seller_ids = set(item.seller_id for item in order_items)

        product_map = {p.id: p.sku for p in self.db.query(Product).filter(Product.id.in_([i.product_id for i in order_items])).all()}

        for seller_id in seller_ids:
            # Create notification in DB
            notification = notif_service.create_seller_notification(
                seller_id=seller_id,
                order_id=order.id,
                payload={
                    "order_id": order.id,
                    "total_amount": order.total_amount,
                    "items": [{"product_id": i.product_id, "sku": product_map.get(i.product_id), "quantity": i.quantity} for i in order_items if i.seller_id == seller_id]
                }
            )

            # Send real-time notification via WebSocket
            await manager.send_to_seller(
                seller_id,
                message={
                    "type": "new_order",
                    "order_id": order.id,
                    "notification_id": notification.id,
                    "payload": notification.payload,
                    "created_at": str(notification.created_at)
                }
            )

        return response

    async def cancel_order(self, order_id: int, current_user: User, background_tasks=BackgroundTasks):
        if current_user.role.value != "customer":
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
        if current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")

        return self.db.query(Order).order_by(Order.created_at.desc()).all()
    
    # ---------------- Seller Methods ---------------- #
    def get_seller_orders(self, current_user: User) -> List[dict]:
        if current_user.role.value != "seller":
            raise HTTPException(status_code=403, detail="Not authorized")

        # Eager-load items + product
        orders = (
            self.db.query(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product)
            )
            .join(OrderItem)
            .filter(OrderItem.seller_id == current_user.id,
                    Order.payment_status == "paid")
            .all()
        )

        if not orders:
            return []

        seller_orders = []
        for order in orders:
            seller_items = [
                {
                    "id": item.id,
                    "product": {
                        "name": item.product.name,
                        "sku": item.product.sku
                    },
                    "seller_id": item.seller_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "status": item.status
                }
                for item in order.items
                if item.seller_id == current_user.id
            ]

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
        if current_user.role.value != "seller":
            raise HTTPException(status_code=403, detail="Not authorized")

        # Eager-load items + product
        order = (
            self.db.query(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product)
            )
            .filter(Order.id == order_id)
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        seller_items = [
            {
                "id": item.id,
                "product": {
                    "name": item.product.name,
                    "sku": item.product.sku
                },
                "seller_id": item.seller_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "status": item.status
            }
            for item in order.items
            if item.seller_id == current_user.id
        ]

        if not seller_items:
            raise HTTPException(
                status_code=403, 
                detail="This order does not contain your products"
            )

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

    def update_order_item_status(
        self, 
        order_id: int, 
        item_id: int, 
        new_status: OrderStatus, 
        current_user: User
    ):
        if current_user.role.value != "seller":
            raise HTTPException(status_code=403, detail="Only sellers can update item status")

        # Include product load
        order_item = (
            self.db.query(OrderItem)
            .options(selectinload(OrderItem.product))
            .filter(
                OrderItem.id == item_id,
                OrderItem.order_id == order_id,
                OrderItem.seller_id == current_user.id
            )
            .first()
        )

        if not order_item:
            raise HTTPException(status_code=404, detail="Item not found for this seller in this order")

        # Prevent changes if order item is cancelled
        if order_item.status == "cancelled":
            raise HTTPException(status_code=400, detail="Cannot change status of a cancelled order item")

        # Restricted transitions
        if order_item.status in ["shipped", "delivered"] and new_status == "pending":
            raise HTTPException(status_code=400, detail="Cannot move shipped/delivered to pending")

        if order_item.status == "delivered" and new_status == "shipped":
            raise HTTPException(status_code=400, detail="Cannot move delivered to shipped")

        # Update status
        order_item.status = new_status
        self.db.commit()

        updated_order = update_order_overall_status(order_id, self.db)
        return updated_order