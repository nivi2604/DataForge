from fastapi import APIRouter

from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])
audit_log_service = AuditLogService()


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs() -> list[AuditLogResponse]:
    # TODO: Implement listing audit logs.
    raise NotImplementedError


@router.get("/{audit_log_id}", response_model=AuditLogResponse)
def get_audit_log(audit_log_id: str) -> AuditLogResponse:
    # TODO: Implement fetching an audit log entry.
    raise NotImplementedError


@router.get("/user/{user_id}", response_model=list[AuditLogResponse])
def get_audit_logs_by_user(user_id: str) -> list[AuditLogResponse]:
    # TODO: Implement fetching audit logs for a user.
    raise NotImplementedError
