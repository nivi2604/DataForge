from fastapi import APIRouter

from app.models.execution_log import ExecutionLog
from app.models.pipeline_execution import PipelineExecution
from app.schemas.execution import ExecutePipelineRequest, ExecutionLogResponse, ExecutionResponse
from app.services.execution_service import ExecutionService

router = APIRouter(tags=["executions"])
execution_service = ExecutionService()


@router.post("/pipelines/{pipeline_id}/execute", response_model=ExecutionResponse)
def execute_pipeline(pipeline_id: str, payload: ExecutePipelineRequest) -> ExecutionResponse:
    # TODO: Implement pipeline execution trigger.
    raise NotImplementedError


@router.get("/executions", response_model=list[ExecutionResponse])
def list_executions() -> list[ExecutionResponse]:
    # TODO: Implement listing executions.
    raise NotImplementedError


@router.get("/executions/{execution_id}", response_model=ExecutionResponse)
def get_execution(execution_id: str) -> ExecutionResponse:
    # TODO: Implement fetching an execution.
    raise NotImplementedError


@router.get("/executions/{execution_id}/logs", response_model=list[ExecutionLogResponse])
def get_execution_logs(execution_id: str) -> list[ExecutionLogResponse]:
    # TODO: Implement fetching execution logs.
    raise NotImplementedError


@router.post("/executions/{execution_id}/cancel", response_model=ExecutionResponse)
def cancel_execution(execution_id: str) -> ExecutionResponse:
    # TODO: Implement cancel execution flow.
    raise NotImplementedError
