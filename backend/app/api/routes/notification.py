from fastapi import APIRouter

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationResponse, NotificationUpdate
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])
notification_service = NotificationService()


@router.get("", response_model=list[NotificationResponse])
def list_notifications() -> list[NotificationResponse]:
    # TODO: Implement listing notifications.
    raise NotImplementedError


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(notification_id: str) -> NotificationResponse:
    # TODO: Implement fetching a notification.
    raise NotImplementedError


@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(notification_id: str) -> NotificationResponse:
    # TODO: Implement marking a notification as read.
    raise NotImplementedError


@router.put("/read-all", response_model=list[NotificationResponse])
def mark_all_notifications_read() -> list[NotificationResponse]:
    # TODO: Implement marking all notifications as read.
    raise NotImplementedError


@router.delete("/{notification_id}")
def delete_notification(notification_id: str) -> dict[str, str]:
    # TODO: Implement deleting a notification.
    raise NotImplementedError
