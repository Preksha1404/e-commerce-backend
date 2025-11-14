import stripe
import logging
import json
from typing import Optional, Dict, Any
from io import BytesIO

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.orders import Order
from src.models.orders import OrderItem
from src.models.orders import OrderStatus
from src.models.payment import Payment, PaymentStatus
from src.models.products import Product
from src.core.stripe_config import get_stripe_client, get_stripe_webhook_secret, get_stripe_currency
from src.schemas.payments import PaymentIntentCreate
from src.services.invoice_generator import generate_pdf

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.stripe = get_stripe_client()
        self.webhook_secret = get_stripe_webhook_secret()
        self.default_currency = get_stripe_currency()

    # -------------------- Payment Intents -------------------- #
    def create_payment_intent(
        self,
        order_id: int,
        currency: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        existing_payment = self.db.query(Payment).filter(Payment.order_id == order_id).first()
        if existing_payment:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment already exists for this order")

        if abs(amount - order.total_amount) > 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order total amount must be greater than 0"
            )

        amount_cents = int(amount * 100)
        currency = currency or self.default_currency

        payment_metadata = {"order_id": str(order_id), "user_id": str(order.user_id)}
        if metadata:
            payment_metadata.update(metadata)

        try:
            payment_intent = self.stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata=payment_metadata,
                automatic_payment_methods={"enabled": True},
            )

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
            logger.error(f"Error creating payment intent: {str(e)}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating payment intent: {str(e)}")

    def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        try:
            payment_intent = self.stripe.PaymentIntent.retrieve(payment_intent_id)
            payment = self.db.query(Payment).filter(Payment.stripe_payment_intent_id == payment_intent_id).first()

            if not payment:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

            status_changed = payment.status != PaymentStatus.SUCCEEDED if payment_intent.status == "succeeded" else False

            if payment_intent.status == "succeeded":
                payment.status = PaymentStatus.SUCCEEDED
                if payment_intent.latest_charge:
                    payment.stripe_charge_id = payment_intent.latest_charge
                if payment_intent.payment_method_types:
                    payment.payment_method = payment_intent.payment_method_types[0]

                order = self.db.query(Order).filter(Order.id == payment.order_id).first()
                if order:
                    if order.payment_status != OrderPaymentStatus.PAID:
                        order.payment_status = OrderPaymentStatus.PAID
                        if status_changed:
                            self._deduct_order_stock(order)

            elif payment_intent.status in ["canceled", "payment_failed"]:
                payment.status = PaymentStatus.FAILED

            self.db.commit()
            self.db.refresh(payment)

            return {"success": payment_intent.status == "succeeded", "payment": payment, "synced": True}

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error confirming payment: {str(e)}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error confirming payment: {str(e)}")

    def _deduct_order_stock(self, order: Order):
        for item in order.items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock -= item.quantity
                if product.stock < 0:
                    product.stock = 0
        self.db.commit()

    # -------------------- Stripe Webhooks -------------------- #
    def handle_webhook_event(self, payload: bytes, signature: str) -> Dict[str, Any]:
        if not self.webhook_secret:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook secret not configured")

        try:
            event = self.stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

        event_type = event["type"]
        event_data = event["data"]["object"]

        if event_type == "payment_intent.succeeded":
            return self._handle_payment_succeeded(event_data)
        elif event_type == "payment_intent.payment_failed":
            return self._handle_payment_failed(event_data)
        else:
            return {"status": "unhandled", "event_type": event_type}

    def _handle_payment_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        payment_intent_id = event_data["id"]
        payment = self.db.query(Payment).filter(Payment.stripe_payment_intent_id == payment_intent_id).first()
        if not payment:
            return {"status": "error", "message": "Payment not found"}

        payment.status = PaymentStatus.SUCCEEDED
        if event_data.get("latest_charge"):
            payment.stripe_charge_id = event_data["latest_charge"]
        if event_data.get("payment_method_types"):
            payment.payment_method = event_data["payment_method_types"][0]

        order = self.db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            order.payment_status = OrderPaymentStatus.PAID
            self._deduct_order_stock(order)

        self.db.commit()
        self.db.refresh(payment)
        return {"status": "success", "payment_id": payment.id, "order_id": payment.order_id}

    def _handle_payment_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        payment_intent_id = event_data["id"]
        payment = self.db.query(Payment).filter(Payment.stripe_payment_intent_id == payment_intent_id).first()
        if not payment:
            return {"status": "error", "message": "Payment not found"}

        payment.status = PaymentStatus.FAILED
        self.db.commit()
        self.db.refresh(payment)
        return {"status": "success", "payment_id": payment.id, "order_id": payment.order_id}

    # -------------------- Payment Queries -------------------- #
    def get_payment_by_id(self, payment_id: int) -> Payment:
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        return payment

    def get_payment_by_order_id(self, order_id: int) -> Optional[Payment]:
        return self.db.query(Payment).filter(Payment.order_id == order_id).first()

    def get_seller_payments(self, seller_id: int) -> list:
        order_items = self.db.query(OrderItem).filter(OrderItem.seller_id == seller_id).all()
        order_ids = list(set(item.order_id for item in order_items))
        payments = self.db.query(Payment).filter(Payment.order_id.in_(order_ids)).all()
        return payments

    # -------------------- Invoice Generation -------------------- #
    def create_payment_invoice(self, order: Order, payment: Payment):
        try:
            invoice_data = {
                "invoice_id": f"INV-{payment.id}",
                "order_id": order.id,
                "user_id": order.user_id,
                "amount": order.total_amount if hasattr(order, 'total_amount') else 0,
                "currency": "USD",
                "payment_status": payment.status.value if hasattr(payment.status, 'value') else payment.status,
                "products": [
                    {
                        "name": item.product.name,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "total_price": item.total_price,
                        "category": item.product.category.name if item.product.category else None,
                        "seller": item.product.seller.name if item.product.seller else None
                    }
                    for item in order.items
                ],
            }

            pdf_buffer = BytesIO()
            generate_pdf(invoice_data, pdf_buffer)
            pdf_buffer.seek(0)

            invoice_file_path = f"generated_invoices/invoice_{invoice_data['invoice_id']}.pdf"
            with open(invoice_file_path, "wb") as f:
                f.write(pdf_buffer.getvalue())

            logger.info(f"Invoice generated: {invoice_file_path}")
            return {"status": "success", "message": "Invoice generated successfully", "invoice_file_path": invoice_file_path}

        except Exception as e:
            logger.error(f"Error generating invoice: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating invoice: {str(e)}")
