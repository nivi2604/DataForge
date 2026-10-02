from fastapi import APIRouter, Header

from app.api.routes.auth import auth_service
from app.core.security import get_current_user
from app.models.execution_log import ExecutionLog
from app.models.pipeline_execution import PipelineExecution
from app.models.user import User
from app.schemas.execution import ExecutePipelineRequest, ExecutionLogResponse, ExecutionResponse
from app.services.execution_service import ExecutionService
from app.services.authorization_service import AuthorizationService

router = APIRouter(tags=["executions"])
execution_service = ExecutionService()


def _require_authentication(authorization: str | None) -> User:
    return get_current_user(authorization, auth_service.user_repository)


def _to_execution_response(execution: PipelineExecution) -> ExecutionResponse:
    return ExecutionResponse(
        id=execution.id or "",
        pipeline_id=execution.pipeline_id,
        status=execution.status,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        duration=execution.duration,
        triggered_by=execution.triggered_by,
        error_message=execution.error_message,
        created_at=execution.created_at,
    )


@router.post("/pipelines/{pipeline_id}/executions", response_model=ExecutionResponse, status_code=201)
def execute_pipeline(
    pipeline_id: str,
    payload: ExecutePipelineRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ExecutionResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)
    if not payload.triggered_by:
        payload.triggered_by = user.email or user.id
    execution = execution_service.execute_pipeline(pipeline_id, payload, user.id)
    return _to_execution_response(execution)


@router.get("/pipelines/{pipeline_id}/executions", response_model=list[ExecutionResponse])
def list_executions(
    pipeline_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> list[ExecutionResponse]:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)
    executions = execution_service.list_executions(pipeline_id)
    return [_to_execution_response(e) for e in executions]


@router.get("/pipelines/{pipeline_id}/executions/{execution_id}", response_model=ExecutionResponse)
def get_execution(
    pipeline_id: str,
    execution_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ExecutionResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)
    execution = execution_service.get_execution(execution_id)
    return _to_execution_response(execution)


def _to_execution_log_response(log: ExecutionLog) -> ExecutionLogResponse:
    return ExecutionLogResponse(
        id=log.id or "",
        execution_id=log.execution_id,
        level=log.level,
        message=log.message,
        timestamp=log.created_at,
    )


@router.get("/pipelines/{pipeline_id}/executions/{execution_id}/logs", response_model=list[ExecutionLogResponse])
def get_execution_logs(
    pipeline_id: str,
    execution_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> list[ExecutionLogResponse]:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)
    logs = execution_service.get_execution_logs(pipeline_id, execution_id)
    return [_to_execution_log_response(log) for log in logs]


@router.post("/pipelines/{pipeline_id}/executions/{execution_id}/cancel", response_model=ExecutionResponse)
def cancel_execution(
    pipeline_id: str,
    execution_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ExecutionResponse:
    _require_authentication(authorization)
    execution = execution_service.cancel_execution(execution_id)
    return _to_execution_response(execution)
