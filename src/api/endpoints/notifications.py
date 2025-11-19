from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.utils.auth import get_current_active_user
from src.services.notification_service import NotificationService
from src.models.users import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/history")
def notifications_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role.value != "seller":
        raise HTTPException(403, "Only sellers can view notifications")

    service = NotificationService(db)
    return service.get_seller_notifications(current_user.id)


@router.patch("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role.value != "seller":
        raise HTTPException(403, "Only sellers can read notifications")

    service = NotificationService(db)
    notif = service.mark_as_read(notification_id, current_user.id)

    if not notif:
        raise HTTPException(404, "Notification not found")

    return {"message": "Notification marked as read"}

@router.patch("/read/all")
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role.value != "seller":
        raise HTTPException(403, "Only sellers can read notifications")

    service = NotificationService(db)
    updated_count = service.mark_all_as_read(current_user.id)

    return {"message": f"{updated_count} notifications marked as read"}