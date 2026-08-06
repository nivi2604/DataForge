from dataclasses import dataclass


@dataclass
class NotificationCreate:
    user_id: str
    title: str
    message: str
    type: str | None = None
    is_read: bool | None = None


@dataclass
class NotificationUpdate:
    title: str | None = None
    message: str | None = None
    type: str | None = None
    is_read: bool | None = None


@dataclass
class NotificationResponse:
    id: str
    user_id: str | None = None
    title: str | None = None
    message: str | None = None
    type: str | None = None
    is_read: bool | None = None
    created_at: str | None = None
