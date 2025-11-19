from sqlalchemy.orm import Session
from src.models.notifications import Notification

class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create_seller_notification(self, seller_id: int, order_id: int = None, payload: dict = None):
        notification = Notification(
            seller_id=seller_id,
            order_id=order_id,
            payload=payload or {},
            type="new_order"
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_seller_notifications(self, seller_id: int):
        return (
            self.db.query(Notification)
            .filter(Notification.seller_id == seller_id)
            .order_by(Notification.created_at.desc())
            .all()
        )

    def mark_as_read(self, notification_id: int, seller_id: int):
        notification = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id, Notification.seller_id == seller_id)
            .first()
        )
        if notification:
            notification.is_read = True
            self.db.commit()
        return notification
    
    def mark_all_as_read(self, seller_id: int) -> int:
        notifications = (
            self.db.query(Notification)
            .filter(Notification.seller_id == seller_id, Notification.is_read == False)
            .all()
        )
        for notif in notifications:
            notif.is_read = True
        self.db.commit()
        return len(notifications)