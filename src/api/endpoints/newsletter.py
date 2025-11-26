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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Subscribe logged-in user to newsletter and send confirmation email"""
    logger.info(f"Newsletter subscribe request from user {current_user.id} with email {payload.email}")
    sub = svc_subscribe(db, payload.email, current_user.id)
    logger.info(f"User {current_user.id} subscribed to newsletter")
    # Send confirmation email
    try:
        logger.info(f"Sending subscription confirmation email to {payload.email}")
        await send_subscription_confirmation_email(background_tasks, payload.email, current_user.full_name or "Subscriber")
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {str(e)}")
        # don't block subscription if email fails
        pass
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



