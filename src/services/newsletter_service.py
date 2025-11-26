from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from src.models.newsletter import NewsletterSubscriber
from src.services.email_service import send_email
from src.utils.email_templates import newsletter_subscription_confirmation_template, coupon_notification_template
import logging

logger = logging.getLogger(__name__)


def subscribe(db: Session, email: str, user_id: Optional[int] = None):
    existing = db.query(NewsletterSubscriber).filter(NewsletterSubscriber.email == email).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
        return existing
    subscriber = NewsletterSubscriber(email=email, user_id=user_id)
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    return subscriber


def unsubscribe(db: Session, email: str):
    existing = db.query(NewsletterSubscriber).filter(NewsletterSubscriber.email == email).first()
    if not existing:
        return None
    existing.is_active = False
    db.commit()
    db.refresh(existing)
    return existing


def list_subscribers(db: Session, active_only: bool = True, limit: int = 100, offset: int = 0) -> List[NewsletterSubscriber]:
    q = db.query(NewsletterSubscriber)
    if active_only:
        q = q.filter(NewsletterSubscriber.is_active == True)
    return q.offset(offset).limit(limit).all()


async def send_subscription_confirmation_email(background_tasks: BackgroundTasks, email: str, user_name: str = "Subscriber"):
    """Send subscription confirmation email to newly subscribed user"""
    try:
        subject, html = newsletter_subscription_confirmation_template(user_name)
        logger.info(f"Sending subscription confirmation email to {email}")
        await send_email(background_tasks, email, subject, html)
        logger.info(f"Subscription confirmation email queued for {email}")
    except Exception as e:
        logger.error(f"Error sending subscription confirmation email to {email}: {str(e)}")


async def notify_subscribers(db: Session, coupon: object, background_tasks: BackgroundTasks, batch_size: int = 50):
    """Send coupon notification emails to all active subscribers"""
    logger.info("=" * 60)
    logger.info("notify_subscribers: STARTING NOTIFICATION PROCESS")
    logger.info(f"Background tasks available: {background_tasks is not None}")
    
    subscribers = db.query(NewsletterSubscriber).filter(NewsletterSubscriber.is_active == True).all()
    total = len(subscribers)
    logger.info(f"notify_subscribers: found {total} active subscribers in database")
    
    if not subscribers:
        logger.warning("notify_subscribers: NO active subscribers found, skipping")
        return

    # Extract coupon details
    coupon_code = getattr(coupon, 'coupon_code', 'SAVE10')
    coupon_name = getattr(coupon, 'coupon_name', 'Special Offer')
    discount_value = getattr(coupon, 'discount_value', 10)
    discount_type = getattr(coupon, 'discount_type', 'percent')
    expiry_date = str(getattr(coupon, 'expiry_date', ''))
    coupon_description = getattr(coupon, 'coupon_description', '')
    
    logger.info(f"Coupon details - code: {coupon_code}, name: {coupon_name}, discount: {discount_value}{discount_type}, expiry: {expiry_date}")

    queued = 0
    failed = 0
    # send in batches to avoid hitting rate limits
    for i in range(0, len(subscribers), batch_size):
        batch = subscribers[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}, size: {len(batch)}")
        for s in batch:
            try:
                logger.info(f"Preparing email for subscriber: {s.email}")
                subject, html = coupon_notification_template(
                    user_name=(s.email.split('@')[0] if s.email else 'Subscriber'),
                    coupon_code=coupon_code,
                    coupon_name=coupon_name,
                    discount_value=discount_value,
                    discount_type=discount_type,
                    expiry_date=expiry_date,
                    coupon_description=coupon_description
                )
                await send_email(background_tasks, s.email, subject, html)
                queued += 1
                logger.info(f"Queued coupon email for subscriber: {s.email}")
            except Exception as e:
                failed += 1
                logger.error(f"Failed to queue coupon email for {s.email}: {str(e)}", exc_info=True)

    logger.info(f"notify_subscribers: COMPLETED - queued {queued}/{total} emails, failed: {failed}")
    logger.info("=" * 60)
