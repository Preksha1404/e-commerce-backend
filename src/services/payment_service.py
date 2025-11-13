import stripe
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from src.models.payments import Payment, PaymentStatus
from src.models.orders import Order, OrderStatus, PaymentStatus as OrderPaymentStatus
from src.models.products import Product
from src.core.stripe_config import (
    get_stripe_client,
    get_stripe_webhook_secret,
    get_stripe_currency
)
import logging
import json

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.stripe = get_stripe_client()
        self.webhook_secret = get_stripe_webhook_secret()
        self.default_currency = get_stripe_currency()

    def create_payment_intent(
        self,
        order_id: int,
        currency: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe payment intent for an order.
        Amount is automatically fetched from the order's total_amount.
        """
        # Verify order exists and is in valid state
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        # Check if payment already exists
        existing_payment = self.db.query(Payment).filter(
            Payment.order_id == order_id
        ).first()
        if existing_payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment already exists for this order"
            )

        # Fetch amount from order's total_amount
        payment_amount = order.total_amount
        
        # Validate order has a valid amount
        if payment_amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order total amount must be greater than 0"
            )

        # Convert amount to cents (Stripe uses smallest currency unit)
        amount_cents = int(payment_amount * 100)
        currency = currency or self.default_currency

        # Prepare metadata
        payment_metadata = {
            "order_id": str(order_id),
            "user_id": str(order.user_id),
        }
        if metadata:
            payment_metadata.update(metadata)

        try:
            # Create Stripe Payment Intent
            payment_intent = self.stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata=payment_metadata,
                automatic_payment_methods={
                    "enabled": True,
                },
            )

            # Create payment record in database
            payment = Payment(
                order_id=order_id,
                stripe_payment_intent_id=payment_intent.id,
                amount=payment_amount,
                currency=currency,
                status=PaymentStatus.PENDING,
                payment_metadata=payment_metadata
            )
            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)

            return {
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": payment_amount,
                "currency": currency,
                "status": payment_intent.status,
                "order_id": order_id
            }

        except Exception as e:
            # Handle Stripe errors
            error_type = type(e).__name__
            if 'Stripe' in error_type or hasattr(e, 'user_message'):
                logger.error(f"Stripe error creating payment intent: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stripe error: {str(e)}"
                )
            else:
                logger.error(f"Error creating payment intent: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error creating payment intent: {str(e)}"
                )

    def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Confirm a payment intent and sync status from Stripe.
        This is useful when webhook wasn't received or processed.
        """
        try:
            logger.info(f"Syncing payment status for payment_intent_id: {payment_intent_id}")
            
            # Retrieve payment intent from Stripe
            payment_intent = self.stripe.PaymentIntent.retrieve(payment_intent_id)
            logger.info(f"Payment intent status from Stripe: {payment_intent.status}")

            # Find payment in database
            payment = self.db.query(Payment).filter(
                Payment.stripe_payment_intent_id == payment_intent_id
            ).first()

            if not payment:
                logger.error(f"Payment not found in database for payment_intent_id: {payment_intent_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found"
                )

            # Track if status changed
            status_changed = payment.status != PaymentStatus.SUCCEEDED if payment_intent.status == "succeeded" else False

            # Update payment status based on Stripe status
            if payment_intent.status == "succeeded":
                # Assign enum object - SQLAlchemy will use the value
                payment.status = PaymentStatus.SUCCEEDED
                if payment_intent.latest_charge:
                    payment.stripe_charge_id = payment_intent.latest_charge
                if payment_intent.payment_method_types:
                    payment.payment_method = payment_intent.payment_method_types[0]

                # Update order payment status
                order = self.db.query(Order).filter(Order.id == payment.order_id).first()
                if order:
                    if order.payment_status != OrderPaymentStatus.PAID:
                        logger.info(f"Updating order {order.id} payment_status to PAID")
                        order.payment_status = OrderPaymentStatus.PAID
                        # Deduct stock only when payment succeeds and status changed
                        if status_changed:
                            logger.info(f"Deducting stock for order {order.id}")
                            self._deduct_order_stock(order)
                    else:
                        logger.info(f"Order {order.id} already marked as PAID, skipping stock deduction")

            elif payment_intent.status == "canceled" or payment_intent.status == "payment_failed":
                payment.status = PaymentStatus.FAILED
                logger.info(f"Payment {payment.id} marked as FAILED")

            self.db.commit()
            self.db.refresh(payment)

            logger.info(f"Payment {payment.id} status synced successfully: {payment.status}")
            return {
                "success": payment_intent.status == "succeeded",
                "message": f"Payment {payment_intent.status}",
                "payment": payment,
                "synced": True
            }

        except Exception as e:
            # Handle both Stripe errors and database errors
            if hasattr(stripe, 'error') and isinstance(e, stripe.error.StripeError):
                logger.error(f"Stripe error confirming payment: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stripe error: {str(e)}"
                )
            else:
                # Database or other errors
                logger.error(f"Error confirming payment: {str(e)}", exc_info=True)
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error confirming payment: {str(e)}"
                )

    def _deduct_order_stock(self, order: Order):
        """
        Deduct stock for order items when payment succeeds.
        """
        for item in order.items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock -= item.quantity
                if product.stock < 0:
                    product.stock = 0  # Prevent negative stock
        self.db.commit()

    def handle_webhook_event(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.
        """
        if not self.webhook_secret:
            logger.error("STRIPE_WEBHOOK_SECRET is not configured. Cannot verify webhook signature.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook secret not configured"
            )
        
        try:
            # Verify webhook signature
            event = self.stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            logger.info(f"Webhook event received: {event.get('type')} (id: {event.get('id')})")
        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload"
            )
        except Exception as e:
            # Check if it's a signature verification error
            error_type = type(e).__name__
            if 'SignatureVerification' in error_type or 'Signature' in error_type:
                logger.error(f"Invalid signature: {str(e)}. Webhook secret may be incorrect.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid signature"
                )
            else:
                # Re-raise if it's a different ValueError
                raise

        # Handle different event types
        event_type = event["type"]
        event_data = event["data"]["object"]

        if event_type == "payment_intent.succeeded":
            return self._handle_payment_succeeded(event_data)
        elif event_type == "payment_intent.payment_failed":
            return self._handle_payment_failed(event_data)

        else:
            logger.info(f"Unhandled event type: {event_type}")
            return {"status": "unhandled", "event_type": event_type}

    def _handle_payment_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle payment_intent.succeeded webhook event.
        """
        payment_intent_id = event_data["id"]
        
        payment = self.db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id
        ).first()

        if not payment:
            logger.error(f"Payment not found for payment_intent_id: {payment_intent_id}")
            return {"status": "error", "message": "Payment not found"}

        # Update payment status
        payment.status = PaymentStatus.SUCCEEDED
        if event_data.get("latest_charge"):
            payment.stripe_charge_id = event_data["latest_charge"]
        if event_data.get("payment_method_types"):
            payment.payment_method = event_data["payment_method_types"][0]

        # Update order payment status
        order = self.db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            order.payment_status = OrderPaymentStatus.PAID
            # Deduct stock only when payment succeeds
            self._deduct_order_stock(order)

        self.db.commit()
        self.db.refresh(payment)

        logger.info(f"Payment succeeded for order {payment.order_id}")
        return {
            "status": "success",
            "message": "Payment processed successfully",
            "payment_id": payment.id,
            "order_id": payment.order_id
        }

    def _handle_payment_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle payment_intent.payment_failed webhook event.
        """
        payment_intent_id = event_data["id"]
        
        payment = self.db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id
        ).first()

        if not payment:
            logger.error(f"Payment not found for payment_intent_id: {payment_intent_id}")
            return {"status": "error", "message": "Payment not found"}

        # Update payment status
        payment.status = PaymentStatus.FAILED

        # Order payment status remains FAILED (already set)
        self.db.commit()
        self.db.refresh(payment)

        logger.info(f"Payment failed for order {payment.order_id}")
        return {
            "status": "success",
            "message": "Payment failure recorded",
            "payment_id": payment.id,
            "order_id": payment.order_id
        }



    def get_payment_by_id(self, payment_id: int) -> Payment:
        """
        Get payment by ID.
        """
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        return payment

    def get_payment_by_order_id(self, order_id: int) -> Optional[Payment]:
        """
        Get payment by order ID.
        """
        return self.db.query(Payment).filter(Payment.order_id == order_id).first()



    def get_seller_payments(self, seller_id: int) -> list:
        """
        Get all payments for orders containing seller's products.
        """
        from src.models.orders import OrderItem

        # Get order IDs that contain seller's products
        order_items = self.db.query(OrderItem).filter(
            OrderItem.seller_id == seller_id
        ).all()

        order_ids = list(set(item.order_id for item in order_items))

        # Get payments for these orders
        payments = self.db.query(Payment).filter(
            Payment.order_id.in_(order_ids)
        ).all()

        return payments

