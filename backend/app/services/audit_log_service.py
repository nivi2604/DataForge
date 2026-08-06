from app.models.audit_log import AuditLog


class AuditLogService:
    """Placeholder audit log service."""

    def list_audit_logs(self) -> list[AuditLog]:
        # TODO: Implement listing audit logs.
        raise NotImplementedError

    def get_audit_log(self, audit_log_id: str) -> AuditLog:
        # TODO: Implement fetching an audit log entry.
        raise NotImplementedError

    def get_audit_logs_by_user(self, user_id: str) -> list[AuditLog]:
        # TODO: Implement fetching audit logs for a user.
        raise NotImplementedError
