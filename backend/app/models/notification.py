from dataclasses import dataclass


@dataclass
class Notification:
    id: str | None = None
    user_id: str | None = None
    title: str | None = None
    message: str | None = None
    type: str | None = None
    is_read: bool | None = None
    created_at: str | None = None
