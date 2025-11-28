from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.schemas.newsletter import NewsletterSubscribe, NewsletterUnsubscribe, NewsletterSubscriberOut
from src.services.newsletter_service import subscribe as svc_subscribe, unsubscribe as svc_unsubscribe, list_subscribers as svc_list_subscribers, send_subscription_confirmation_email
from src.utils.auth import get_current_active_user
from src.models.users import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/newsletter", tags=["Newsletter"])


@router.post('/subscribe', response_model=NewsletterSubscriberOut)
async def subscribe(
    payload: NewsletterSubscribe,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Subscribe any user to newsletter"""
    logger.info(f"Newsletter subscribe request for email {payload.email}")

    # User ID is always None since login is not required
    sub = svc_subscribe(db, payload.email, user_id=None)
    logger.info(f"Email {payload.email} subscribed to newsletter")

    # Always send with default name
    user_name = "Subscriber"

    # Send confirmation email
    try:
        await send_subscription_confirmation_email(
            background_tasks,
            payload.email,
            user_name
        )
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {str(e)}")

    return sub


@router.post('/unsubscribe')
def unsubscribe(payload: NewsletterUnsubscribe, db: Session = Depends(get_db)):
    """Unsubscribe from newsletter (public endpoint, no auth required for convenience)"""
    unsub = svc_unsubscribe(db, payload.email)
    if not unsub:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"message": "Unsubscribed successfully"}


@router.get('/subscribers', response_model=list[NewsletterSubscriberOut])
def list_subscribers(
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user)
):
    """List active newsletter subscribers (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    subs = svc_list_subscribers(db, active_only=True, limit=limit, offset=offset)
    return subs



