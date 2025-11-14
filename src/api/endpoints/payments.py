from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
from src.core.database import get_db
from src.models.users import User
from src.utils.auth import get_current_active_user, require_admin
from src.services.payment_service import PaymentService
from src.schemas.payments import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentResponse,
    PaymentConfirmRequest,
    PaymentConfirmResponse
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payment", tags=["Payments"])


# ------------------- Customer Endpoints ------------------- #
@router.post("/create-intent", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_intent(
    payment_data: PaymentIntentCreate,
    # current_user: User = Depends(get_current_active_user),  # COMMENTED OUT FOR TESTING
    db: Session = Depends(get_db),
):
    if current_user.role.value != "customer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only customers can create payment intents")

    from src.models.orders import Order
    order = db.query(Order).filter(Order.id == payment_data.order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    service = PaymentService(db)
    result = service.create_payment_intent(
        order_id=payment_data.order_id,
        currency=payment_data.currency,
        metadata=payment_data.metadata
    )
    return PaymentIntentResponse(**result)


@router.post("/confirm", response_model=PaymentConfirmResponse)
def confirm_payment(
    confirm_data: PaymentConfirmRequest,
    # current_user: User = Depends(get_current_active_user),  # COMMENTED OUT FOR TESTING
    db: Session = Depends(get_db),
):
    if current_user.role.value != "customer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only customers can confirm payments")

    service = PaymentService(db)
    result = service.confirm_payment(confirm_data.payment_intent_id)
    return PaymentConfirmResponse(**result)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    service = PaymentService(db)
    payment = service.get_payment_by_id(payment_id)

    if current_user.role.value == "customer":
        from src.models.orders import Order
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        if not order or order.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this payment")
    return payment


@router.get("/order/{order_id}", response_model=PaymentResponse)
def get_payment_by_order(order_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    service = PaymentService(db)
    payment = service.get_payment_by_order_id(order_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found for this order")

    if current_user.role.value == "customer":
        from src.models.orders import Order
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or order.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this payment")
    return payment


# ------------------- Stripe Webhook ------------------- #
@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    if not stripe_signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing stripe-signature header")

    payload = await request.body()
    service = PaymentService(db)

    try:
        result = service.handle_webhook_event(payload, stripe_signature)
        logger.info(f"Webhook processed successfully: {result.get('status', 'unknown')}")

        if result.get("type") == "payment_intent.succeeded":
            create_payment_invoice(result, db)

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing webhook: {str(e)}")


# ------------------- Seller Endpoints ------------------- #
@router.get("/seller/orders/{order_id}/payment", response_model=PaymentResponse)
def get_seller_order_payment(order_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if current_user.role.value != "seller":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only sellers can view order payments")

    from src.models.orders import Order, OrderItem
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id, OrderItem.seller_id == current_user.id).all()
    if not order_items:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This order does not contain your products")

    service = PaymentService(db)
    payment = service.get_payment_by_order_id(order_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found for this order")
    return payment


@router.get("/seller/payments", response_model=list[PaymentResponse])
def get_seller_payments(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if current_user.role.value != "seller":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only sellers can view their payments")

    service = PaymentService(db)
    payments = service.get_seller_payments(current_user.id)
    return payments


# ------------------- Admin Endpoints ------------------- #
@router.get("/admin/payments", response_model=list[PaymentResponse])
def get_all_payments(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    from models.payment import Payment
    payments = db.query(Payment).order_by(Payment.created_at.desc()).all()
    return payments


@router.post("/admin/sync-pending-payments")
def sync_pending_payments(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    from models.payment import Payment, PaymentStatus
    import stripe

    service = PaymentService(db)
    pending_payments = db.query(Payment).filter(Payment.status == PaymentStatus.PENDING).all()

    synced, failed = [], []

    for payment in pending_payments:
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)

            if payment_intent.status == "succeeded" and payment.status != PaymentStatus.SUCCEEDED:
                result = service.confirm_payment(payment.stripe_payment_intent_id)
                synced.append({"payment_id": payment.id, "order_id": payment.order_id, "status": "synced", "result": result})
            elif payment_intent.status in ["canceled", "payment_failed"] and payment.status != PaymentStatus.FAILED:
                payment.status = PaymentStatus.FAILED
                db.commit()
                synced.append({"payment_id": payment.id, "order_id": payment.order_id, "status": "synced", "stripe_status": payment_intent.status})
        except Exception as e:
            logger.error(f"Failed to sync payment {payment.id}: {str(e)}")
            failed.append({"payment_id": payment.id, "order_id": payment.order_id, "error": str(e)})

    return {
        "total_pending": len(pending_payments),
        "synced": len(synced),
        "failed": len(failed),
        "synced_payments": synced,
        "failed_payments": failed
    }
