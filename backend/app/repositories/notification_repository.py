from app.models.notification import Notification


class NotificationRepository:
    """Placeholder notification repository."""

    def list_notifications(self) -> list[Notification]:
        # TODO: Implement repository logic for listing notifications.
        raise NotImplementedError

    def get_notification(self, notification_id: str) -> Notification:
        # TODO: Implement repository logic for fetching a notification.
        raise NotImplementedError

    def create_notification(self, notification: Notification) -> Notification:
        # TODO: Implement repository logic for creating a notification.
        raise NotImplementedError

    def update_notification(self, notification_id: str, notification: Notification) -> Notification:
        # TODO: Implement repository logic for updating a notification.
        raise NotImplementedError

    def delete_notification(self, notification_id: str) -> None:
        # TODO: Implement repository logic for deleting a notification.
        raise NotImplementedError
