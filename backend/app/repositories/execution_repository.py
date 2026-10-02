from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.execution_log import ExecutionLog
from app.models.pipeline_execution import PipelineExecution


class ExecutionRepository:
    """Execution repository."""

    def create_execution(self, execution: PipelineExecution) -> PipelineExecution:
        if not execution.id:
            execution.id = str(uuid4())

        if not execution.created_at:
            execution.created_at = datetime.now(timezone.utc).isoformat()

        with SessionLocal() as session:
            session.add(execution)
            session.commit()
            session.refresh(execution)
            return execution

    def list_executions(self, pipeline_id: str | None = None) -> list[PipelineExecution]:
        with SessionLocal() as session:
            query = session.query(PipelineExecution)
            if pipeline_id:
                query = query.filter(PipelineExecution.pipeline_id == pipeline_id)
            return list(query.all())

    def get_execution(self, execution_id: str) -> PipelineExecution | None:
        with SessionLocal() as session:
            return session.get(PipelineExecution, execution_id)

    def get_execution_logs(self, execution_id: str) -> list[ExecutionLog]:
        with SessionLocal() as session:
            return list(
                session.query(ExecutionLog)
                .filter(ExecutionLog.execution_id == execution_id)
                .order_by(ExecutionLog.created_at.asc())
                .all()
            )

    def create_execution_log(self, log: ExecutionLog) -> ExecutionLog:
        if not log.id:
            log.id = str(uuid4())
        if not log.created_at:
            log.created_at = datetime.now(timezone.utc).isoformat()

        with SessionLocal() as session:
            session.add(log)
            session.commit()
            session.refresh(log)
            return log

    def update_execution(self, execution_id: str, execution: PipelineExecution) -> PipelineExecution:
        with SessionLocal() as session:
            existing = session.get(PipelineExecution, execution_id)
            if not existing:
                raise KeyError(execution_id)

            for field in ["status", "started_at", "completed_at", "duration", "error_message"]:
                value = getattr(execution, field, None)
                if value is not None:
                    setattr(existing, field, value)

            session.commit()
            session.refresh(existing)
            return existing
