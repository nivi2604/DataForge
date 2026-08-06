from dataclasses import dataclass


@dataclass
class AuditLogResponse:
    id: str
    user_id: str | None = None
    action: str | None = None
    resource: str | None = None
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: str | None = None
