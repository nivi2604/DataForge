from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate


class NotificationService:
    """Placeholder notification service."""

    def list_notifications(self) -> list[Notification]:
        # TODO: Implement listing notifications.
        raise NotImplementedError

    def get_notification(self, notification_id: str) -> Notification:
        # TODO: Implement fetching a notification.
        raise NotImplementedError

    def create_notification(self, payload: NotificationCreate) -> Notification:
        # TODO: Implement creating a notification.
        raise NotImplementedError

    def mark_notification_read(self, notification_id: str) -> Notification:
        # TODO: Implement marking a notification as read.
        raise NotImplementedError

    def mark_all_notifications_read(self) -> list[Notification]:
        # TODO: Implement marking all notifications as read.
        raise NotImplementedError

    def delete_notification(self, notification_id: str) -> None:
        # TODO: Implement deleting a notification.
        raise NotImplementedError
